from pymongo import MongoClient
import csv
import re
import json
from bson.objectid import ObjectId

def connect_to_database():
    client = MongoClient("mongodb+srv://rm550870:080305@visionaryai.5teri.mongodb.net/")
    db = client['VisionaryAI']
    return db['empresas']

def validar_dados_empresa(company_data):
    # Valida CNPJ (14 dígitos numéricos)
    if not re.fullmatch(r"\d{14}", company_data.get('CNPJ', '')):
        return False, "CNPJ inválido. Deve conter exatamente 14 dígitos numéricos."
    
    # Valida nm_empresa (mínimo de 3 caracteres alfanuméricos)
    if not re.fullmatch(r"[a-zA-Z0-9]{3,}", company_data.get('nm_empresa', '')):
        return False, "Nome da empresa inválido. Deve conter pelo menos 3 caracteres alfanuméricos."
    
    # Valida st_empresa (somente 'Ativo' ou 'Inativo')
    if company_data.get('st_empresa') not in ['Ativo', 'Inativo']:
        return False, "Status da empresa inválido. Deve ser 'Ativo' ou 'Inativo'."
    
    # Valida tp_empresa (apenas letras, mínimo de 5 caracteres)
    if not re.fullmatch(r"[a-zA-Z]{5,}", company_data.get('tp_empresa', '')):
        return False, "Tipo de empresa inválido. Deve conter apenas letras e ter no mínimo 5 caracteres."
    
    # Valida ds_email (deve ter formato de email básico)
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", company_data.get('ds_email', '')):
        return False, "E-mail inválido. Deve estar em um formato válido de email."
    
    return True, "Dados válidos."

def generate_unique_id(collection):
    """Gera um ID numérico único que ainda não foi utilizado."""
    existing_ids = {int(company['id_empresa']) for company in collection.find({}, {"id_empresa": 1})}
    new_id = 0
    while new_id in existing_ids:
        new_id += 1  # Incrementa até encontrar um ID livre
    return str(new_id)

def is_unique_field(collection, field_name, value):
    """Verifica se o valor do campo é único na coleção."""
    return collection.count_documents({field_name: value}) == 0

def add_company(collection, company_data):
    valid, msg = validar_dados_empresa(company_data)
    if not valid:
        print(f"Cadastramento inválido: {msg}")
        return
    
    # Verifica se o CNPJ e o nome da empresa são únicos
    if not is_unique_field(collection, 'CNPJ', company_data['CNPJ']):
        print("CNPJ já cadastrado.")
        return
    if not is_unique_field(collection, 'nm_empresa', company_data['nm_empresa']):
        print("Nome da empresa já cadastrado.")
        return

    company_data['id_empresa'] = generate_unique_id(collection)
    result = collection.insert_one(company_data)
    print(f"Empresa adicionada com sucesso! ID: {result.inserted_id}")

def show_companies(collection):
    companies = list(collection.find())
    if companies:
        for company in companies:
            company['_id'] = str(company['_id'])  # Convert ObjectId to string
            print(company)  # Exibe as informações da empresa
    else:
        print("Nenhuma empresa encontrada.")

def update_company(collection):
    id_empresa = input("Informe o ID da empresa para atualização: ")
    field = input("Digite o campo para atualizar (CNPJ, nm_empresa, st_empresa, tp_empresa, ds_email, nr_funcionarios): ")
    new_value = input(f"Digite o novo valor para {field}: ")

    # Verifica se o novo valor do CNPJ ou nome da empresa é único
    if field == 'CNPJ' and not is_unique_field(collection, 'CNPJ', new_value):
        print("CNPJ já cadastrado. Atualização não realizada.")
        return
    if field == 'nm_empresa' and not is_unique_field(collection, 'nm_empresa', new_value):
        print("Nome da empresa já cadastrado. Atualização não realizada.")
        return

    result = collection.update_one(
        {'id_empresa': id_empresa},
        {'$set': {field: new_value}}
    )
    if result.modified_count > 0:
        print("Empresa atualizada com sucesso!")
    else:
        print("Nenhuma empresa encontrada com esse ID ou dados não modificados.")

def delete_company(collection):
    id_empresa = input("Informe o ID da empresa para exclusão: ")
    result = collection.delete_one({'id_empresa': id_empresa})
    if result.deleted_count > 0:
        print("Empresa excluída com sucesso!")
    else:
        print("Nenhuma empresa encontrada com esse ID.")

def export_dados_empresas(collection):
    try:
        companies = list(collection.find({}, {"id_empresa": 1, "CNPJ": 1, "nm_empresa": 1, "st_empresa": 1, "tp_empresa": 1, "ds_email": 1, "nr_funcionarios": 1}))
        
        # Cria arquivo 'empresas.csv' com os dados exportados
        with open('empresas.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID Empresa", "CNPJ", "Nome Empresa", "Status", "Tipo Empresa", "Email", "Número de Funcionários"])
            for company in companies:
                writer.writerow([
                    company.get('id_empresa', ''),
                    company.get('CNPJ', ''),
                    company.get('nm_empresa', ''),
                    company.get('st_empresa', ''),
                    company.get('tp_empresa', ''),
                    company.get('ds_email', ''),
                    company.get('nr_funcionarios', '')
                ])
        print("Dados das empresas exportados com sucesso para 'empresas.csv'.")
    except Exception as e:
        print(f"Ocorreu um erro ao exportar os dados: {e}")

def show_external_json_data(filepath):
    """Lê e exibe dados de um arquivo JSON externo."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print("Dados do arquivo JSON:")
            for entry in data:
                print(entry)
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo JSON: {e}")

def main_menu():
    collection = connect_to_database()

    while True:
        print("\nSelecione uma opção:")
        print("1. Adicionar empresa")
        print("2. Exibir empresas")
        print("3. Atualizar empresa")
        print("4. Excluir empresa")
        print("5. Exportar dados das empresas")
        print("6. Visualizar dados do arquivo JSON externo")
        print("7. Sair")
        option = input("Escolha o número da operação desejada: ")

        if option == '1':
            company_data = {
                "CNPJ": input("CNPJ (14 dígitos): "),
                "nm_empresa": input("Nome da empresa (mínimo 3 caracteres): "),
                "st_empresa": input("Status (Ativo/Inativo): "),
                "tp_empresa": input("Tipo de empresa (mínimo 5 letras): "),
                "ds_email": input("Email da empresa: "),
                "nr_funcionarios": int(input("Número de funcionários: "))
            }
            add_company(collection, company_data)
        elif option == '2':
            show_companies(collection)
        elif option == '3':
            update_company(collection)
        elif option == '4':
            delete_company(collection)
        elif option == '5':
            export_dados_empresas(collection)
        elif option == '6':
            show_external_json_data('/workspaces/Sprint4-DB/Python/arquivo json/empresas.json')
        elif option == '7':
            print("Encerrando...")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main_menu()
