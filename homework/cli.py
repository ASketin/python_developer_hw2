from homework.patient import Patient, db_request

import click


@click.group()
def cli():
    pass


@click.command()
@click.argument("name")
@click.argument("surname")
@click.option("--birth-date")
@click.option("--phone")
@click.option("--document-type")
@click.option("--document-number", type=(str, str))
def create(name, surname, birth_date,
           phone, document_type, document_number):
    patient = Patient(name, surname, birth_date, phone,
                      document_type, document_number[0] + document_number[1])
    patient.save()


@click.command()
@click.argument("limit", default=10)
def show(limit):
    for patient in db_request(f"select * from {Patient.table} limit {limit}", "many"):
        print(*patient[1:])


@click.command()
def count():
    result = db_request(f"select Count(*) from {Patient.table}", "one")
    print("Amount of stored patients: ", result[0])


cli.add_command(create)
cli.add_command(show)
cli.add_command(count)

if __name__ == "__main__":
    cli()
