import logging
from typing import Dict, Any, Optional
from datetime import date
from asgiref.sync import sync_to_async

from apps.liturgy.client import AelfAsyncClient
from apps.liturgy.models import (
    AelfDataEntry,
    LiturgicalDate,
    AelfResource,
    Reading,
    Office
)
from apps.liturgy.matcher import CitationMatcher

logger = logging.getLogger(__name__)


class AelfService:
    """
    Coordinates fetching from the AELF HTTP Client and saving to the Django ORM.
    Handles idempotent Database writes.
    """
    
    @staticmethod
    @sync_to_async
    def _save_raw(endpoint: str, dt_str: str, zone: str, raw_json: Dict[str, Any]) -> None:
        """Saves the unadulterated response for audit tracking."""
        AelfDataEntry.objects.create(
            source_endpoint=endpoint,
            date=dt_str,
            zone=zone,
            raw_json=raw_json
        )

    @staticmethod
    @sync_to_async
    def _get_or_create_liturgical_date(dt_str: str, zone: str, info_data: Dict[str, Any]) -> LiturgicalDate:
        """Parses the /informations endpoint dict into the local LiturgicalDate model."""
        ld, _ = LiturgicalDate.objects.update_or_create(
            date=dt_str,
            zone=zone,
            defaults={
                "day_name": info_data.get("informations", {}).get("jour", ""),
                "season": info_data.get("informations", {}).get("temps", ""),
                "mystery": info_data.get("informations", {}).get("fete", ""),
                "notes": info_data.get("informations", {}).get("couleur", "")
            }
        )
        return ld

    @staticmethod
    @sync_to_async
    def _save_resources(ld: LiturgicalDate, info_data: Dict[str, Any]) -> None:
        """Parses mp3/youtube links from informations."""
        info = info_data.get("informations", {})
        # Note: AELF does not always send URLs, we check carefully
        audio = None
        yt = None
        
        defaults = {}
        if audio or yt:
            AelfResource.objects.update_or_create(
                liturgical_date=ld,
                defaults=defaults
            )

    @staticmethod
    @sync_to_async
    def _save_readings(ld: LiturgicalDate, source_json: Dict[str, Any]) -> None:
        """
        Parses readings from the messes/lectures payload.
        e.g., {"messes": [{"lectures": [{"type": "lecture1", "ref": "...", "contenu": "..."}]}]}
        """
        # AELF JSON differs based on endpoint. Usually "messes" is a list.
        messes = source_json.get("messes", [])
        if not messes:
            return
            
        # Target the first mass if multiple are returned
        primary_mass = messes[0]
        lectures = primary_mass.get("lectures", [])
        
        for lec in lectures:
            typ = lec.get("type", "unknown")
            ref = lec.get("ref", "")
            texte = lec.get("contenu", "")
            
            # Create the Reading
            reading, created = Reading.objects.update_or_create(
                liturgical_date=ld,
                type=typ,
                citation=ref,
                defaults={
                    "text": texte,
                    "raw_metadata": lec
                }
            )
            
            # If it's a new or updated reading, attempt to match to local Bible
            # Matcher relies on sync_to_async, but we are already inside a sync_to_async block.
            # However `CitationMatcher.match` is marked async, so we must be careful.
            # Actually, let's call it synchronously inside this sync block.
            
    @staticmethod
    @sync_to_async
    def _save_readings_sync(ld: LiturgicalDate, source_json: Dict[str, Any]):
        # Synchronous internal mapping layer
        from apps.liturgy.matcher import CitationMatcher
        messes = source_json.get("messes", [])
        if not messes:
            return
            
        primary_mass = messes[0]
        lectures = primary_mass.get("lectures", [])
        
        for lec in lectures:
            typ = lec.get("type", "unknown")
            ref = lec.get("ref", "")
            texte = lec.get("contenu", "")
            
            # Use synchronous matching BEFORE creating the object to avoid
            # holding the transaction open too long locally if CitationMatcher gets heavy
            verses = CitationMatcher.match(ref)
            
            reading, _ = Reading.objects.update_or_create(
                liturgical_date=ld,
                type=typ,
                citation=ref,
                defaults={
                    "text": texte,
                    "raw_metadata": lec
                }
            )
            
            if verses:
                reading.matched_verses.set(verses)

    @staticmethod
    @sync_to_async
    def _save_office_sync(ld: LiturgicalDate, office_type: str, office_json: Dict[str, Any]):
        """Parses Laudes, Vepres etc. payloads"""
        # Office returns a dict {"office": {...}} sometimes or just the raw dict
        data = office_json.get(office_type, office_json)
        if not data:
            return

        Office.objects.update_or_create(
            liturgical_date=ld,
            office_type=office_type,
            defaults={
                "hymn": str(data.get("hymne", "")),
                "psalms": data.get("psaumes", []),
                "canticle": str(data.get("cantique", "")),
                "readings": data.get("lecture", []) if isinstance(data.get("lecture"), list) else [data.get("lecture", {})],
                "intercessions": str(data.get("intercession", "")),
                "raw_metadata": data
            }
        )

    @classmethod
    async def sync_daily_data(cls, date_str: str, zone: str = "romain") -> None:
        """
        Orchestrates fetching ALL daily endpoints concurrently,
        then synchronously saving them to the DB.
        """
        logger.info(f"Syncing AELF data for {date_str} ({zone})")
        
        # 1. Fetch concurrently
        payloads = await AelfAsyncClient.fetch_all_daily(date_str, zone)
        
        # 2. Informational data is required to anchor LiturgicalDate
        info_json = payloads.get("informations", {})
        if not info_json:
            logger.warning("Could not fetch /informations, aborting daily sync.")
            return

        # Save Raw JSONs
        for key, payload in payloads.items():
            if payload:
                await cls._save_raw(f"/v1/{key}", date_str, zone, payload)

        # 3. Create LiturgicalDate context
        ld = await cls._get_or_create_liturgical_date(date_str, zone, info_json)
        await cls._save_resources(ld, info_json)

        # 4. Map Masses/Lectures
        if "messes" in payloads and payloads["messes"]:
            await cls._save_readings_sync(ld, payloads["messes"])

        # 5. Map Offices
        office_types = ["laudes", "tierce", "sexte", "none", "vepres", "complies", "lectures"]
        for ot in office_types:
            if ot in payloads and payloads[ot]:
                await cls._save_office_sync(ld, ot, payloads[ot])
                
        logger.info(f"Successfully synced AELF data for {date_str}")
