from app.parsers.document_parser import DocumentParser

def test_parse():
    parser = DocumentParser()
    
    pth = "D:/Projects/ChatML/data/test/3df12ef1-25b7-4c46-b339-fbc08f032925/YOLO_v1.pdf"
    elements = parser.parse(pth)

    assert len(elements) > 0
    assert elements[0].source == "YOLO_v1.pdf"

test_parse()