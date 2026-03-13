from django.test import TestCase

from apps.tv.utils.youtube import extract_youtube_video_id


class YoutubeUtilsTests(TestCase):
    def test_extract_id_watch_url(self):
        video_id = extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_extract_id_short_url(self):
        video_id = extract_youtube_video_id("https://youtu.be/5NV6Rdv1a3I")
        self.assertEqual(video_id, "5NV6Rdv1a3I")

    def test_extract_id_embed_url(self):
        video_id = extract_youtube_video_id("https://www.youtube.com/embed/MtN1YnoL46Q")
        self.assertEqual(video_id, "MtN1YnoL46Q")

    def test_extract_id_invalid_url(self):
        video_id = extract_youtube_video_id("https://example.com/video/123")
        self.assertIsNone(video_id)
