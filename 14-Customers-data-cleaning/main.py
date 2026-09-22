import phonenumbers
from phonenumbers import geocoder, timezone, carrier, PhoneNumberType, NumberParseException

map = {}

def phone_info(raw, region='UA'):
    try: 
        phone = phonenumbers.parse(raw, region)
        if not phonenumbers.is_valid_number(phone):
            return None
        else:
            map['type'] = phonenumbers.number_type(phone)
            map['country'] = geocoder.country_name_for_number(phone, 'en')
            map['carrier'] = carrier.name_for_number(phone, 'en')
            map['timezone'] = timezone.time_zones_for_number(phone)
            return map
    except NumberParseException:
        return None

print(phone_info("+380671234567"))
print(phone_info("not a phone"))