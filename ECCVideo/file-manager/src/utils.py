import _pickle as cPickle
import io
import mimetypes
from urllib import request
import uuid

class MultiPartForm:
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        # Use a large random byte string to separate
        # parts of the MIME data.
        self.boundary = uuid.uuid4().hex.encode('utf-8')
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary={}'.format(
            self.boundary.decode('utf-8'))

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, fileHandle,
                 mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = (
                mimetypes.guess_type(filename)[0] or
                'application/octet-stream'
            )
        self.files.append((fieldname, filename, mimetype, body))
        return

    @staticmethod
    def _form_data(name):
        return ('Content-Disposition: form-data; '
                'name="{}"\r\n').format(name).encode('utf-8')

    @staticmethod
    def _attached_file(name, filename):
        return ('Content-: file; '
                'name="{}"; filename="{}"\r\n').format(
                    name, filename).encode('utf-8')

    @staticmethod
    def _content_type(ct):
        return 'Content-Type: {}\r\n'.format(ct).encode('utf-8')

    def __bytes__(self):
        """Return a byte-string representing the form data,
        including attached files.
        """
        buffer = io.BytesIO()
        boundary = b'--' + self.boundary + b'\r\n'

        # Add the form fields
        for name, value in self.form_fields:
            # buffer.write(boundary)
            # buffer.write(self._form_data(name))
            # buffer.write(b'\r\n')
            buffer.write(value.encode('utf-8'))
            # buffer.write(b'\r\n')

        # Add the files to upload
        for f_name, filename, f_content_type, body in self.files:
            # buffer.write(boundary)
            # buffer.write(self._attached_file(f_name, filename))
            # buffer.write(self._content_type(f_content_type))
            # buffer.write(b'\r\n')
            buffer.write(body)
            # buffer.write(b'\r\n')

        # buffer.write(b'--' + self.boundary + b'--\r\n')
        return buffer.getvalue()

# kwargs has key: object_path or contents
def upload_file(puturl, object_name, **kwargs):
    form = MultiPartForm()
    if 'contents' in kwargs:
        form.add_file(
            'contents', object_name,
            fileHandle=io.BytesIO(cPickle.dumps(kwargs['contents'])))
    elif 'object_path' in kwargs:
        form.add_file(
            'contents', object_name,
            fileHandle=open(kwargs['object_path'],'rb'))
    data = bytes(form)
    r = request.Request(puturl, data=data,method='PUT')
    r.add_header('Content-type', form.get_content_type())
    r.add_header('Content-length', len(data))
    request.urlopen(r)