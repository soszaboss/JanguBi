import logging

from django.db import connection

logger = logging.getLogger(__name__)


class IndexService:
    """Service handling PostgreSQL specific full-text indexing."""

    @staticmethod
    def populate_tsv_for_book(book_id: int) -> int:
        """
        Updates the tsvector field for all verses in a given book.
        Uses raw SQL for maximum performance with Postgres to_tsvector.
        Uses the 'french' dictionary.
        Returns the number of rows updated.
        """
        query = """
            UPDATE bible_verse
            SET tsv = to_tsvector('french', text)
            WHERE chapter_id IN (
                SELECT id FROM bible_chapter WHERE book_id = %s
            )
        """
        logger.info(f"Populating TSV index for book_id {book_id}")
        
        with connection.cursor() as cursor:
            cursor.execute(query, [book_id])
            rowcount = cursor.rowcount
            
        logger.info(f"Populated TSV for {rowcount} verses in book_id {book_id}")
        return rowcount

    @staticmethod
    def populate_tsv_all() -> int:
        """Updates TSV for all verses. Useful for initial setup or dictionary changes."""
        query = """
            UPDATE bible_verse
            SET tsv = to_tsvector('french', text)
        """
        logger.info("Populating TSV index for ALL verses")
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            rowcount = cursor.rowcount
            
        logger.info(f"Populated TSV for {rowcount} verses total")
        return rowcount
