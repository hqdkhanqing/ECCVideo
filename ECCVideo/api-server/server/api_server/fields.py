from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import JSONField
from django.utils import six
import json

class ArrayField(JSONField):
    def to_internal_value(self, data):
        try:
            if self.binary or getattr(data, 'is_json_string', False):
                if isinstance(data, six.binary_type):
                    data = data.decode('utf-8')
                result=json.loads(data)
                if isinstance(result,list):
                    result=list(map(str,result))
                    result = list(set(result))
                    result.sort()
                    return result
                else:
                  self.fail('invalid')
            else:
                json.dumps(data)
            if isinstance(data,list):
                data=list(map(str,data))
                data = list(set(data))
                data.sort()
                return data
            else:
              self.fail('invalid')
        except (TypeError, ValueError):
            self.fail('invalid')