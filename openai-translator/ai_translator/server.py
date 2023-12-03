from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import os
from model import OpenAIModel
from translator import PDFTranslator

INDEX_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload File</title>
</head>
<body>
    <h2>Upload File</h2>
    <input type="file" id="fileToUpload">
    <button onclick="uploadFile()">Upload File</button>
    <button onclick="translateFile()">exec translate</button>
    <button onclick="downloadFile()">Download translated File</button>
</body>
<script>
    function uploadFile() {
        var file = document.getElementById('fileToUpload').files[0];

        // Create a FormData object and append the file
        var formData = new FormData();
        formData.append('file', file);

        // Create an AJAX request
        var xhr = new XMLHttpRequest();
        xhr.open('POST', 'api/upload', true);

        // Define what happens on successful data submission
        xhr.onload = function () {
            if (xhr.status == 200) {
                alert('File successfully uploaded');
            } else {
                alert('Upload failed');
            }
        };

        // Send the FormData object with the file
        xhr.send(formData);
    }

    function translateFile() {
        // Create an AJAX request
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'api/translate', true);

        // Define what happens on successful data submission
        xhr.onload = function () {
            if (xhr.status == 200) {
                alert('File successfully translated');
            } else {
                alert('translate failed');
            }
        };

        xhr.send();
    }

    function downloadFile() {
        var link = document.createElement('a');
        link.href = 'api/download'; // Replace with the path to the file you want to download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
</script>
</html>
'''
model_name = 'gpt-3.5-turbo'
api_key = 'sk-xxx'
pdf_file_path='tempfile/origin.pdf'
file_format = 'markdown'
target_language = '中文'
output_file_path = 'tempfile/translated.md'
def translate_pdf():
    model = OpenAIModel(model=model_name, api_key=api_key)
    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    translator = PDFTranslator(model)
    translator.translate_pdf(pdf_file_path, file_format, target_language, output_file_path)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        url = urlparse(self.path)
        if url.path == '/api/upload':
            # Check if the request is a file upload
            if self.headers['content-type'].startswith('multipart/form-data'):
                # Parse the form data contained in the request
                form = cgi.FieldStorage(
                    fp=self.rfile, 
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': self.headers['Content-Type'],
                    })

                # Check if a field named 'file' is provided in the form
                if 'file' in form:
                    file_item = form['file']

                    # Check if the file item is not empty
                    if file_item.filename:
                        # It's a regular file, save it
                        os.makedirs('tempfile', exist_ok=True)
                        file_path = pdf_file_path
                        if os.path.exists(file_path):
                            # If it exists, remove it
                            os.remove(file_path)
                        with open(file_path, 'wb') as output_file:
                            output_file.write(file_item.file.read())
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"File uploaded successfully.")
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"No file was uploaded.")
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Missing 'file' in form data.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Incorrect MIME type: expected 'multipart/form-data'.")

    def do_GET(self):
        # Parse the URL and the query parameters
        url = urlparse(self.path)

        # Handle the root path
        if url.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(INDEX_PAGE, 'utf8'))

        elif url.path == '/api/translate':
            translate_pdf()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'translated successfully')
        elif url.path == '/api/download':
            file_name = 'translated.md'
            with open(output_file_path, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{file_name}"')
                self.end_headers()
                self.wfile.write(file.read())

        # Handle other paths
        else:
            self.send_response(404)  # Not Found
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'404 Not Found')

# Set the port number
port = 8000

# Create the server object
httpd = HTTPServer(('localhost', port), SimpleHTTPRequestHandler)

# Run the server
print(f"Server started at http://localhost:{port}")
httpd.serve_forever()
