import faker

faker  = faker.Faker()

def fake_data_gen():
    return {
        "name": faker.name(),
        "address": faker.address(),
        "email": faker.email(),
        "date_of_birth": str(faker.date_of_birth()),
        "phone_number": faker.phone_number(),
        "job": faker.job(),
        "company": faker.company(),
        "text": faker.text()
    }

print(fake_data_gen())