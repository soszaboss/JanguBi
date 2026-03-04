import datetime
from typing import List, Dict, Optional
from collections import defaultdict
import calendar

from django.db.models import QuerySet
from django.utils import timezone
from apps.availability.models import (
    Minister,
    ServiceType,
    WeeklyAvailability,
    SpecialAvailability,
    BlockedSlot,
    Booking,
)


class AvailabilityService:
    @staticmethod
    def _chunk_availability(
        start_time: datetime.time,
        end_time: datetime.time,
        duration_minutes: int,
        service_type: ServiceType
    ) -> List[Dict]:
        """
        Subdivides a time boundary into discrete slots of duration_minutes.
        """
        slots = []
        # Convert to datetime on a dummy day to do easy math
        dummy_date = datetime.date.today()
        current = datetime.datetime.combine(dummy_date, start_time)
        end_dt = datetime.datetime.combine(dummy_date, end_time)
        delta = datetime.timedelta(minutes=duration_minutes)

        while current + delta <= end_dt:
            slot_end = current + delta
            slots.append({
                "start": current.time(),
                "end": slot_end.time(),
                "service": service_type.slug,
                "service_name": service_type.name,
            })
            current = slot_end
            
        return slots

    @staticmethod
    def _is_overlapping(
        chunk_start: datetime.time,
        chunk_end: datetime.time,
        block_start: datetime.time,
        block_end: datetime.time
    ) -> bool:
        """
        Returns True if the time periods strictly overlap.
        """
        return chunk_start < block_end and chunk_end > block_start

    def get_available_slots(self, minister_slug: str, date: datetime.date) -> List[Dict]:
        """
        Calculates all perfectly discrete, unblocked slots for a given minister on a specific date.
        """
        try:
            minister = Minister.objects.get(slug=minister_slug, is_active=True)
        except Minister.DoesNotExist:
            return []

        weekly = list(WeeklyAvailability.objects.filter(
            minister=minister,
            weekday=date.weekday(),
            is_active=True
        ).select_related('service_type'))

        special = list(SpecialAvailability.objects.filter(
            minister=minister,
            date=date
        ).select_related('service_type'))

        blocks = list(BlockedSlot.objects.filter(
            minister=minister,
            date=date
        ))

        bookings = list(Booking.objects.filter(
            minister=minister,
            date=date,
            status=Booking.Status.CONFIRMED
        ))

        return self._calculate_slots(weekly, special, blocks, bookings)

    def _calculate_slots(self, weekly, special, blocks, bookings) -> List[Dict]:
        """
        Core logic abstracted for reuse in month calendar.
        """
        raw_chunks = []
        
        # 1. Generate all raw chunks from continuous bounds
        for w in weekly:
            raw_chunks.extend(self._chunk_availability(w.start_time, w.end_time, w.service_type.duration_minutes, w.service_type))
            
        for s in special:
            raw_chunks.extend(self._chunk_availability(s.start_time, s.end_time, s.service_type.duration_minutes, s.service_type))
            
        # Deduplicate raw chunks (if a special overlaps a weekly for same service)
        unique_raw = {}
        for c in raw_chunks:
            key = (c["start"], c["end"], c["service"])
            unique_raw[key] = c
            
        raw_chunks = list(unique_raw.values())
        
        # 2. Filter out any overlapping blocks or bookings
        valid_slots = []
        for chunk in raw_chunks:
            is_blocked = False
            for block in blocks:
                if self._is_overlapping(chunk["start"], chunk["end"], block.start_time, block.end_time):
                    is_blocked = True
                    break
            
            if is_blocked:
                continue
                
            for booking in bookings:
                if self._is_overlapping(chunk["start"], chunk["end"], booking.start_time, booking.end_time):
                    is_blocked = True
                    break
                    
            if not is_blocked:
                # Format to strings for JSON API
                valid_slots.append({
                    "start": chunk["start"].strftime("%H:%M"),
                    "end": chunk["end"].strftime("%H:%M"),
                    "service": chunk["service"],
                    "service_name": chunk["service_name"]
                })
                
        # 3. Sort by start time
        valid_slots.sort(key=lambda x: x["start"])
        return valid_slots

    def get_available_ministers(self, date: datetime.date, service_slug: str) -> QuerySet[Minister]:
        """
        Returns a list of ministers who have at least ONE unblocked slot on the given date for the service.
        """
        # Doing this efficiently in Python rather than complex raw SQL for ease of maintenance.
        # Fetch all active ministers
        ministers = Minister.objects.filter(is_active=True)
        
        # Optimization: Pre-filter by those who even have matching weekly or special rules 
        # (reduces N greatly before computing overlaps)
        valid_minister_ids = set()
        
        weekly_m_ids = WeeklyAvailability.objects.filter(
            weekday=date.weekday(), 
            is_active=True,
            service_type__slug=service_slug
        ).values_list('minister_id', flat=True)
        
        special_m_ids = SpecialAvailability.objects.filter(
            date=date,
            service_type__slug=service_slug
        ).values_list('minister_id', flat=True)
        
        candidate_ids = set(weekly_m_ids).union(set(special_m_ids))
        
        if not candidate_ids:
            return Minister.objects.none()
            
        # Further evaluate overlaps to ensure at least one slot actually exists
        from collections import defaultdict
        
        all_weekly = list(WeeklyAvailability.objects.filter(
            minister_id__in=candidate_ids,
            weekday=date.weekday(),
            is_active=True
        ).select_related('service_type'))
        
        all_special = list(SpecialAvailability.objects.filter(
            minister_id__in=candidate_ids,
            date=date
        ).select_related('service_type'))
        
        all_blocks = list(BlockedSlot.objects.filter(
            minister_id__in=candidate_ids,
            date=date
        ))
        
        all_bookings = list(Booking.objects.filter(
            minister_id__in=candidate_ids,
            date=date,
            status=Booking.Status.CONFIRMED
        ))
        
        w_map = defaultdict(list)
        for w in all_weekly: w_map[w.minister_id].append(w)
            
        s_map = defaultdict(list)
        for s in all_special: s_map[s.minister_id].append(s)
            
        b_blocks_map = defaultdict(list)
        for b in all_blocks: b_blocks_map[b.minister_id].append(b)
            
        b_bookings_map = defaultdict(list)
        for b in all_bookings: b_bookings_map[b.minister_id].append(b)
        
        for minister_id in candidate_ids:
            w_avail = w_map[minister_id]
            s_avail = s_map[minister_id]
            b_blocks = b_blocks_map[minister_id]
            b_bookings = b_bookings_map[minister_id]
            
            slots = self._calculate_slots(w_avail, s_avail, b_blocks, b_bookings)
            service_slots = [s for s in slots if s["service"] == service_slug]
            if service_slots:
                valid_minister_ids.add(minister_id)
                
        return Minister.objects.filter(id__in=valid_minister_ids)

    def compute_month_calendar(self, minister_slug: str, month_str: str) -> Dict:
        """
        Given a month (YYYY-MM), computes day categorizations by loading data efficiently into memory.
        Returns {"available_days": [...], "full_days": [...], "partial_days": [...]}
        """
        try:
            year, month = map(int, month_str.split('-'))
            start_date = datetime.date(year, month, 1)
            _, last_day = calendar.monthrange(year, month)
            end_date = datetime.date(year, month, last_day)
        except ValueError:
            return {"available_days": [], "full_days": [], "partial_days": []}
            
        try:
            minister = Minister.objects.get(slug=minister_slug, is_active=True)
        except Minister.DoesNotExist:
            return {"available_days": [], "full_days": [], "partial_days": []}

        # 1. Broadly pre-fetch all needed data
        all_weekly = list(WeeklyAvailability.objects.filter(
            minister=minister,
            is_active=True
        ).select_related('service_type'))
        
        all_special = list(SpecialAvailability.objects.filter(
            minister=minister,
            date__range=[start_date, end_date]
        ).select_related('service_type'))
        
        all_blocks = list(BlockedSlot.objects.filter(
            minister=minister,
            date__range=[start_date, end_date]
        ))
        
        all_bookings = list(Booking.objects.filter(
            minister=minister,
            date__range=[start_date, end_date],
            status=Booking.Status.CONFIRMED
        ))

        # Group data into memory by relevant day criteria
        weekly_map = defaultdict(list)
        for w in all_weekly:
            weekly_map[w.weekday].append(w)
            
        special_map = defaultdict(list)
        for s in all_special:
            special_map[s.date].append(s)
            
        blocks_map = defaultdict(list)
        for b in all_blocks:
            blocks_map[b.date].append(b)
            
        bookings_map = defaultdict(list)
        for bk in all_bookings:
            bookings_map[bk.date].append(bk)

        result = {
            "available_days": [],
            "full_days": [],
            "partial_days": []
        }

        # 2. Iterate each day
        for day in range(1, last_day + 1):
            current_dt = datetime.date(year, month, day)
            
            w_avail = weekly_map[current_dt.weekday()]
            s_avail = special_map[current_dt]
            b_blocks = blocks_map[current_dt]
            b_bookings = bookings_map[current_dt]
            
            # Use inner service logic
            # To know capacity, we first compute total raw theoretical chunks
            raw_chunks = []
            for w in w_avail:
                raw_chunks.extend(self._chunk_availability(w.start_time, w.end_time, w.service_type.duration_minutes, w.service_type))
            for s in s_avail:
                raw_chunks.extend(self._chunk_availability(s.start_time, s.end_time, s.service_type.duration_minutes, s.service_type))
                
            unique_raw = {}
            for c in raw_chunks:
                unique_raw[(c["start"], c["end"], c["service"])] = c
                
            total_possible_slots = len(unique_raw)
            
            if total_possible_slots == 0:
                continue # Day was just genuinely empty, no scheduled hours.

            valid_slots = self._calculate_slots(w_avail, s_avail, b_blocks, b_bookings)
            
            dt_str = current_dt.strftime("%Y-%m-%d")
            
            if len(valid_slots) == 0:
                result["full_days"].append(dt_str)
            elif len(valid_slots) == total_possible_slots:
                result["available_days"].append(dt_str)
            else:
                result["partial_days"].append(dt_str)
                
        return result
