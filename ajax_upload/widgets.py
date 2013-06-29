from django import forms
from django.conf import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import urllib2

from .models import UploadedFile


class AjaxUploadException(Exception):
    pass


class AjaxClearableFileInput(forms.ClearableFileInput):
    #template_with_clear = ''  # We don't need this
    initial_text = 'Currently' #shouldn't need to do this
    template_with_initial = '<span class="ajax-upload-initial">%(initial_text)s: %(initial)s %(clear_template)s<br /></span>%(input_text)s: %(input)s'

    def render(self, name, value, attrs=None):
        attrs = attrs or {}
        if value:
            if hasattr(value, 'url'):
                filename = value.url
            else:
                filename = u'%s%s' % (settings.MEDIA_URL, value)
        else:
            filename = ''
        attrs.update({
            'class': attrs.get('class', '') + 'ajax-upload',
            'data-filename': filename,  # This is so the javascript can get the actual value
            'data-required': self.is_required or '',
            'data-upload-url': reverse('ajax-upload')
        })
        if filename and not self.is_required:
            attrs['data-clear-name'] = self.clear_checkbox_name(name)
        output = super(AjaxClearableFileInput, self).render(name, value, attrs)
        return mark_safe(output)
    
    def value_from_datadict(self, data, files, name):
        # If a file was uploaded or the clear checkbox was checked, use that.
        file = super(AjaxClearableFileInput, self).value_from_datadict(data, files, name)
        if file is not None:  # super class may return a file object, False, or None
            return file  # Default behaviour
        elif name in data:  # This means a file path was specified in the POST field
            file_path = data.get(name)
            if not file_path:
                return False  # False means clear the existing file
            elif isinstance(file_path, File):
                raise AjaxUploadException('data should not have a file object')
            else:
                relative_path = urllib2.unquote(file_path.encode('utf8')).decode('utf8')
                try:
                    uploaded_file = UploadedFile.objects.get(file=relative_path)
                except UploadedFile.DoesNotExist:
                    # Leave the file unchanged (it could be the original file path)
                    return None
                else:
                    return File(uploaded_file.file)
        return None

