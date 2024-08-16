from faker import Faker
import datetime

fake = Faker()

def generate_fake_data():

    timestamp = datetime.datetime.now(datetime.timezone.utc)
    timestamp_plus_10 = timestamp + datetime.timedelta(minutes=10)
    # Format both datetime objects into strings
    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')
    formatted_timestamp_plus_10 = timestamp_plus_10.strftime('%Y-%m-%d %H:%M:%S %Z')


    return {
        'name': fake.name(),
        'address': fake.address(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'job': fake.job(),
        'company': fake.company(),
        'text': fake.text(),
        'timestamp': formatted_timestamp,
        'session_end': formatted_timestamp_plus_10
    }

print(generate_fake_data())