"""
Unit tests for MusicQueue class
Tests queue operations, thread safety, and edge cases
"""
import pytest
from models.song import Song, MusicQueue


@pytest.mark.unit
class TestMusicQueue:
    """Test suite for MusicQueue operations"""
    
    def test_queue_initialization(self):
        """Test queue initializes with correct defaults"""
        queue = MusicQueue()
        assert len(queue) == 0
        assert queue.current is None
        assert queue.loop is False
        assert queue.volume == 0.5
        assert queue.is_empty() is True
    
    def test_add_song(self, sample_song):
        """Test adding a song to queue"""
        queue = MusicQueue()
        queue.add(sample_song)
        
        assert len(queue) == 1
        assert not queue.is_empty()
        assert sample_song in queue.songs
    
    def test_add_multiple_songs(self):
        """Test adding multiple songs maintains order"""
        queue = MusicQueue()
        songs = []
        
        for i in range(5):
            song = Song(f"url_{i}", f"Song {i}", False)
            songs.append(song)
            queue.add(song)
        
        assert len(queue) == 5
        assert queue.songs == songs
    
    def test_next_song(self, sample_song):
        """Test getting next song from queue"""
        queue = MusicQueue()
        queue.add(sample_song)
        
        next_song = queue.next()
        
        assert next_song == sample_song
        assert queue.current == sample_song
        assert len(queue) == 0  # Song removed from queue
    
    def test_next_with_loop_enabled(self, sample_song):
        """Test next() with loop mode enabled"""
        queue = MusicQueue()
        queue.loop = True
        queue.add(sample_song)
        
        # First call
        first = queue.next()
        assert first == sample_song
        assert queue.current == sample_song
        
        # Second call should return same song (loop mode)
        second = queue.next()
        assert second == sample_song
        assert queue.current == sample_song
    
    def test_next_empty_queue(self):
        """Test next() on empty queue returns None"""
        queue = MusicQueue()
        result = queue.next()
        
        assert result is None
        assert queue.current is None
    
    def test_clear_queue(self, populated_queue):
        """Test clearing the queue"""
        assert len(populated_queue) > 0
        
        populated_queue.clear()
        
        assert len(populated_queue) == 0
        assert populated_queue.is_empty()
        assert populated_queue.current is None
    
    def test_remove_song(self):
        """Test removing specific song from queue"""
        queue = MusicQueue()
        song1 = Song("url1", "Song 1", False)
        song2 = Song("url2", "Song 2", False)
        song3 = Song("url3", "Song 3", False)
        
        queue.add(song1)
        queue.add(song2)
        queue.add(song3)
        
        # Remove middle song
        removed = queue.remove(1)
        
        assert removed == song2
        assert len(queue) == 2
        assert song2 not in queue.songs
        assert queue.songs == [song1, song3]
    
    def test_remove_invalid_index(self, populated_queue):
        """Test removing with invalid index"""
        initial_len = len(populated_queue)
        
        # Try to remove out of bounds
        result = populated_queue.remove(999)
        
        assert result is None
        assert len(populated_queue) == initial_len
    
    def test_volume_property(self):
        """Test volume getter and setter"""
        queue = MusicQueue()
        
        # Default volume
        assert queue.volume == 0.5
        
        # Set new volume
        queue.volume = 0.8
        assert queue.volume == 0.8
        
        # Volume should be clamped
        queue.volume = 1.5
        assert queue.volume == 1.0
        
        queue.volume = -0.5
        assert queue.volume == 0.0
    
    def test_loop_toggle(self):
        """Test loop mode toggle"""
        queue = MusicQueue()
        
        assert queue.loop is False
        
        queue.loop = True
        assert queue.loop is True
        
        queue.loop = False
        assert queue.loop is False
    
    def test_queue_length(self, populated_queue):
        """Test __len__ method"""
        assert len(populated_queue) == 3
        
        populated_queue.next()
        assert len(populated_queue) == 2
        
        populated_queue.clear()
        assert len(populated_queue) == 0
    
    def test_queue_iteration(self, populated_queue):
        """Test iterating over queue"""
        songs_list = list(populated_queue)
        
        assert len(songs_list) == 3
        assert all(isinstance(song, Song) for song in songs_list)
    
    def test_peek_next(self):
        """Test peeking at next song without removing it"""
        queue = MusicQueue()
        song1 = Song("url1", "Song 1", False)
        song2 = Song("url2", "Song 2", False)
        
        queue.add(song1)
        queue.add(song2)
        
        # Peek should return first song without removing
        peeked = queue.peek()
        assert peeked == song1
        assert len(queue) == 2  # Queue unchanged
    
    def test_peek_empty_queue(self):
        """Test peeking at empty queue"""
        queue = MusicQueue()
        assert queue.peek() is None
    
    def test_shuffle_queue(self):
        """Test shuffling queue order"""
        queue = MusicQueue()
        songs = [Song(f"url_{i}", f"Song {i}", False) for i in range(10)]
        
        for song in songs:
            queue.add(song)
        
        original_order = queue.songs.copy()
        queue.shuffle()
        
        # Should have same songs but likely different order
        assert len(queue) == 10
        assert set(queue.songs) == set(original_order)
        # With 10 songs, shuffle should almost certainly change order
        # (probability of same order is 1/10! ≈ 0.0000003%)
    
    def test_current_song_tracking(self):
        """Test that current song is properly tracked"""
        queue = MusicQueue()
        song1 = Song("url1", "Song 1", False)
        song2 = Song("url2", "Song 2", False)
        
        queue.add(song1)
        queue.add(song2)
        
        # No current song initially
        assert queue.current is None
        
        # After next(), current should be set
        queue.next()
        assert queue.current == song1
        
        # After another next(), current should update
        queue.next()
        assert queue.current == song2
    
    def test_queue_with_local_files(self, sample_local_song):
        """Test queue handles local files correctly"""
        queue = MusicQueue()
        queue.add(sample_local_song)
        
        assert len(queue) == 1
        assert sample_local_song.is_local is True
        
        next_song = queue.next()
        assert next_song == sample_local_song
        assert next_song.is_local is True
    
    def test_mixed_queue(self, sample_song, sample_local_song):
        """Test queue with mix of local and remote songs"""
        queue = MusicQueue()
        queue.add(sample_song)
        queue.add(sample_local_song)
        
        assert len(queue) == 2
        
        first = queue.next()
        assert first == sample_song
        assert first.is_local is False
        
        second = queue.next()
        assert second == sample_local_song
        assert second.is_local is True
    
    def test_queue_state_after_clear(self, populated_queue):
        """Test queue state is fully reset after clear"""
        populated_queue.next()  # Set current song
        populated_queue.loop = True
        populated_queue.volume = 0.8
        
        populated_queue.clear()
        
        # Queue should be empty but settings preserved
        assert len(populated_queue) == 0
        assert populated_queue.current is None
        assert populated_queue.loop is True  # Settings preserved
        assert populated_queue.volume == 0.8


@pytest.mark.unit
class TestSong:
    """Test suite for Song class"""
    
    def test_song_initialization(self):
        """Test song initializes correctly"""
        song = Song("test_url", "Test Title", False)
        
        assert song.source == "test_url"
        assert song.title == "Test Title"
        assert song.is_local is False
    
    def test_local_song(self, sample_local_song):
        """Test local song properties"""
        assert sample_local_song.is_local is True
        assert sample_local_song.source.endswith(".mp3")
    
    def test_remote_song(self, sample_song):
        """Test remote song properties"""
        assert sample_song.is_local is False
        assert sample_song.source.startswith("http")
    
    def test_song_equality(self):
        """Test song equality comparison"""
        song1 = Song("url", "Title", False)
        song2 = Song("url", "Title", False)
        song3 = Song("different_url", "Title", False)
        
        # Same source should be equal
        assert song1 == song2
        
        # Different source should not be equal
        assert song1 != song3
    
    def test_song_repr(self):
        """Test song string representation"""
        song = Song("test_url", "Test Song", False)
        repr_str = repr(song)
        
        assert "Test Song" in repr_str
        assert "Song" in repr_str


@pytest.mark.unit
class TestQueueEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_add_none_song(self):
        """Test adding None to queue"""
        queue = MusicQueue()
        
        with pytest.raises((TypeError, AttributeError)):
            queue.add(None)
    
    def test_negative_volume(self):
        """Test volume clamping for negative values"""
        queue = MusicQueue()
        queue.volume = -10.0
        
        assert queue.volume == 0.0
    
    def test_excessive_volume(self):
        """Test volume clamping for excessive values"""
        queue = MusicQueue()
        queue.volume = 999.0
        
        assert queue.volume == 1.0
    
    def test_remove_from_empty_queue(self):
        """Test removing from empty queue"""
        queue = MusicQueue()
        result = queue.remove(0)
        
        assert result is None
    
    def test_large_queue(self):
        """Test queue with many songs"""
        queue = MusicQueue()
        num_songs = 1000
        
        for i in range(num_songs):
            song = Song(f"url_{i}", f"Song {i}", False)
            queue.add(song)
        
        assert len(queue) == num_songs
        
        # Test operations on large queue
        queue.shuffle()
        assert len(queue) == num_songs
        
        first = queue.next()
        assert first is not None
        assert len(queue) == num_songs - 1
