import pytest
import time
from unittest.mock import MagicMock, patch
import queue

from services.queue_service import EmailQueue

class TestEmailQueue:
    def test_enqueue(self):
        """Test adding an email to the queue"""
        # Create a queue
        email_queue = EmailQueue(worker_count=1)
        
        # Enqueue an email
        email_queue.enqueue(1, 2)
        
        # Verify email is in queue
        assert email_queue.queue.qsize() == 1
        priority, email_id = email_queue.queue.get()
        assert priority == 2
        assert email_id == 1
    
    def test_priority_ordering(self):
        """Test that emails are ordered by priority"""
        # Create a queue
        email_queue = EmailQueue(worker_count=1)
        
        # Enqueue emails with different priorities
        email_queue.enqueue(1, 3)  # Medium priority
        email_queue.enqueue(2, 1)  # High priority
        email_queue.enqueue(3, 5)  # Low priority
        
        # Verify they come out in priority order
        priority1, email_id1 = email_queue.queue.get()
        priority2, email_id2 = email_queue.queue.get()
        priority3, email_id3 = email_queue.queue.get()
        
        assert priority1 == 1 and email_id1 == 2  # Highest priority first
        assert priority2 == 3 and email_id2 == 1
        assert priority3 == 5 and email_id3 == 3  # Lowest priority last
    
    @patch('threading.Thread')
    def test_start_workers(self, mock_thread):
        """Test starting worker threads"""
        # Create a queue with mock email service
        email_queue = EmailQueue(worker_count=2)
        email_queue.email_service = MagicMock()
        
        # Start workers
        email_queue.start_workers()
        
        # Verify threads were created and started
        assert mock_thread.call_count == 2
        assert mock_thread.return_value.start.call_count == 2
        assert email_queue.running is True
    
    def test_stop_workers(self):
        """Test stopping worker threads"""
        # Create a queue
        import threading
        email_queue = EmailQueue(worker_count=1)
        email_queue.running = True
        
        # Create mock threads
        mock_thread1 = MagicMock()
        mock_thread2 = MagicMock()
        email_queue.workers = [mock_thread1, mock_thread2]
        
        # Patch the join method to avoid actual waiting
        with patch.object(threading.Thread, 'join', return_value=None):
            # Stop workers
            email_queue.stop_workers()
            
            # Verify running flag is set to False
            assert email_queue.running is False
            
            # Verify join was attempted on worker threads
            mock_thread1.join.assert_called_once()
            mock_thread2.join.assert_called_once()
            
            # Verify workers list is empty
            assert email_queue.workers == []
        
    @patch('time.sleep', return_value=None)  # Don't actually sleep in tests
    def test_worker_process(self, mock_sleep):
        """Test the worker process function"""
        # Create a queue with mock email service
        email_queue = EmailQueue(worker_count=1)
        email_queue.email_service = MagicMock()
        email_queue.email_service.process_queued_email.return_value = True
        
        # Add an email to the queue
        email_queue.enqueue(1, 1)
        
        # Start the worker process in a way we can control
        email_queue.running = True
        
        # Run one iteration of the worker process
        with patch.object(queue.PriorityQueue, 'get', return_value=(1, 1)):
            email_queue._worker_process(0)
            
        # Verify email was processed
        email_queue.email_service.process_queued_email.assert_called_once_with(1)
        
        # Verify queue task was marked as done
        assert email_queue.queue.task_done.called
    
    @patch('time.sleep', return_value=None)
    def test_worker_process_failure(self, mock_sleep):
        """Test worker process handling a failed email"""
        # Create a queue with mock email service
        email_queue = EmailQueue(worker_count=1)
        email_queue.email_service = MagicMock()
        email_queue.email_service.process_queued_email.return_value = False
        
        # Add an email to the queue
        email_queue.enqueue(1, 1)
        
        # Start the worker process in a way we can control
        email_queue.running = True
        
        # Run one iteration of the worker process
        with patch.object(queue.PriorityQueue, 'get', return_value=(1, 1)):
            email_queue._worker_process(0)
            
        # Verify email was processed
        email_queue.email_service.process_queued_email.assert_called_once_with(1)
        
        # Verify failed email was handled
        email_queue.email_service.handle_failed_email.assert_called_once_with(1, email_queue.max_retries)