from unittest.mock import patch, MagicMock
import pytest
from app.services.parsing_service import ParsingService

def test_parsing_service_success():
    # Mock Path.exists to return True
    with patch("app.services.parsing_service.Path.exists", return_value=True):
        # Mock partition to return dummy elements
        mock_el1 = MagicMock()
        mock_el1.__str__.return_value = "Hello World"
        mock_el1.metadata.page_number = 1
        
        mock_el2 = MagicMock()
        mock_el2.__str__.return_value = "   "  # should be skipped
        
        mock_el3 = MagicMock()
        mock_el3.__str__.return_value = "Second Page"
        mock_el3.metadata = MagicMock(spec=[]) # doesn't have page_number attribute
        
        with patch("app.services.parsing_service.partition", return_value=[mock_el1, mock_el2, mock_el3]) as mock_partition:
            service = ParsingService(strategy="fast", languages=["eng"])
            results = service.parse("dummy_path.pdf")
            
            mock_partition.assert_called_once_with(
                filename="dummy_path.pdf",
                strategy="fast",
                languages=["eng"]
            )
            
            assert len(results) == 2
            assert results[0].text == "Hello World"
            assert results[0].page_number == 1
            assert results[0].source == "dummy_path.pdf"
            
            assert results[1].text == "Second Page"
            assert results[1].page_number is None
            assert results[1].source == "dummy_path.pdf"

def test_parsing_service_file_not_found():
    with patch("app.services.parsing_service.Path.exists", return_value=False):
        service = ParsingService()
        with pytest.raises(FileNotFoundError):
            service.parse("nonexistent.pdf")

if __name__ == "__main__":
    test_parsing_service_success()
    test_parsing_service_file_not_found()
    print("ParsingService tests passed successfully!")
