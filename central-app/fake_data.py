from faker import Faker

fake = Faker()

def generate_fake_data():
    return {
        'name': fake.name(),
        'address': fake.address(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'job': fake.job(),
        'company': fake.company(),
        'text': fake.text(),
    }

name, address, email, phone, job, company, text = generate_fake_data().values()
print(name)
print(address)
print(email)
print(phone)
print(job)
print(company)
print(text)