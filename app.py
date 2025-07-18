import os
import zipfile
import json
import shutil
import uuid
import traceback
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory

# Importa as funções e variáveis do módulo preview corrigido
from preview_final_v3 import (
    TEXTURE_MAPPING, 
    VANILLA_PREVIEW_MAP_PYTHON,
    analyze_resource_pack_with_defaults,
    initialize_vanilla_preview_map,
    load_default_zip_textures,
    format_minecraft_text
)

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-insegura') # MUDE ISSO PARA UMA CHAVE SEGURA!

# Configurações de pastas
UPLOAD_FOLDER = 'uploads'
GENERATED_PACKS_FOLDER = 'generated_packs'
TEMP_PREVIEW_FOLDER = 'temp_previews'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_PACKS_FOLDER, exist_ok=True)
os.makedirs(TEMP_PREVIEW_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_PACKS_FOLDER'] = GENERATED_PACKS_FOLDER
app.config['TEMP_PREVIEW_FOLDER'] = TEMP_PREVIEW_FOLDER
app.config['APP_ROOT'] = os.path.dirname(os.path.abspath(__file__))

# --- Rota da Página Inicial ---
@app.route('/')
def index():
    # Limpa a sessão e as pastas temporárias ao iniciar
    if 'uploaded_packs' in session:
        for pack_id in session['uploaded_packs']:
            pack_dir = os.path.join(app.config['TEMP_PREVIEW_FOLDER'], pack_id)
            if os.path.exists(pack_dir):
                shutil.rmtree(pack_dir)
    session.clear()
    return render_template('index.html')

# --- Rota para Upload de Packs ---
@app.route('/upload', methods=['POST'])
def upload_packs():
    if 'texture_packs' not in request.files:
        return render_template('index.html', error="Nenhum arquivo enviado.")

    files = request.files.getlist('texture_packs')
    if not files or files[0].filename == '':
        return render_template('index.html', error="Nenhum arquivo selecionado.")

    uploaded_packs_data = []
    all_item_types = set() # Para coletar todos os tipos de itens disponíveis em todos os packs

    # Certifica-se de que a lista de packs na sessão existe
    if 'uploaded_packs' not in session:
        session['uploaded_packs'] = []

    # Armazena os dados dos packs na sessão para uso posterior
    if 'uploaded_packs_data' not in session:
        session['uploaded_packs_data'] = []

    for file in files:
        if file and file.filename.endswith('.zip'):
            pack_upload_id = str(uuid.uuid4())
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{pack_upload_id}.zip")
            file.save(filepath)

            # Usa a nova função que inclui suporte ao default.zip
            pack_analysis = analyze_resource_pack_with_defaults(
                filepath, 
                pack_upload_id, 
                app.config['TEMP_PREVIEW_FOLDER'],
                app.config['APP_ROOT']
            )
            
            if pack_analysis:
                original_file_name = file.filename
                pack_analysis['formatted_name'] = original_file_name
                # Outras preparações...
                uploaded_packs_data.append(pack_analysis)
                session['uploaded_packs'].append(pack_analysis['id']) # Armazena apenas o ID
                session['uploaded_packs_data'].append(pack_analysis)  # Armazena dados completos
                
                # Adiciona os tipos de itens encontrados neste pack ao conjunto global
                for item_type in pack_analysis['available_textures'].keys():
                    all_item_types.add(item_type)
                    
                print(f"Pack {file.filename} processado com sucesso:")
                print(f"  - Texturas disponíveis: {len(pack_analysis['available_textures'])}")
                user_count = sum(1 for t in pack_analysis['available_textures'].values() if not t.get('is_default', False))
                default_count = len(pack_analysis['available_textures']) - user_count
                print(f"  - Do usuário: {user_count}, Padrão: {default_count}")
            else:
                # Se a análise falhar, remove o arquivo zip e o ID da sessão
                if os.path.exists(filepath):
                    os.remove(filepath)
                if pack_upload_id in session['uploaded_packs']:
                    session['uploaded_packs'].remove(pack_upload_id)
                print(f"ERRO CRÍTICO ao salvar ou analisar o arquivo {file.filename}")
                return render_template('index.html', error=f"Erro ao processar o pack: {file.filename}. Por favor, tente novamente.")
        else:
            return render_template('index.html', error="Apenas arquivos .zip são permitidos.")

    # Converte o conjunto de tipos de itens para uma lista ordenada
    all_item_types_list = sorted(list(all_item_types), key=lambda x: list(TEXTURE_MAPPING.keys()).index(x) if x in TEXTURE_MAPPING else len(TEXTURE_MAPPING))

    # Converte o dicionário VANILLA_PREVIEW_MAP_PYTHON para uma string JSON segura
    vanilla_preview_map_json_string = json.dumps(VANILLA_PREVIEW_MAP_PYTHON)

    print(f"Upload concluído. {len(uploaded_packs_data)} packs processados.")
    print(f"Total de tipos de itens únicos: {len(all_item_types_list)}")
    textures_dict = {}
    if uploaded_packs_data:
        # Exemplo: pega apenas do PRIMEIRO pack enviado
        textures_dict = uploaded_packs_data[0].get("available_textures", {})
        # OU, para mergear de vários packs, pode juntar manualmente se seu JS espera tudo junto
    return render_template('selection.html', 
                           uploaded_packs_data=uploaded_packs_data, 
                           all_item_types=all_item_types_list,
                           vanilla_preview_map_json_string=vanilla_preview_map_json_string,
                           textures_dict=textures_dict)

# --- Rota para Gerar o Pack Personalizado ---
@app.route('/generate', methods=['POST'])
def generate_pack():
    selected_textures = {}
    
    # Pega o caminho da skin padrão
    default_skin_path = request.form.get('default_skin_path', 'steve.png') # Valor padrão se não for enviado

    # Itera sobre os dados do formulário para encontrar as seleções de textura
    # O nome do campo é 'select_{itemType.replace(" ", "_")}'
    for field_name, selected_pack_id in request.form.items():
        if field_name.startswith('select_'):
            # Converte o nome do campo de volta para o friendly_name
            # Ex: 'select_Espada_de_Diamante' -> 'Espada de Diamante'
            item_type = field_name.replace('select_', '').replace('_', ' ')
            
            # Verifica se o itemType existe no TEXTURE_MAPPING para garantir que é um item válido
            if item_type in TEXTURE_MAPPING:
                # Se 'default' for selecionado, usamos a textura vanilla.
                # O caminho interno será o primeiro caminho da lista no TEXTURE_MAPPING.
                if selected_pack_id == 'default':
                    # Para texturas vanilla, precisamos do caminho interno original
                    # Ex: 'block/white_wool.png'
                    # Assumimos que o primeiro path no TEXTURE_MAPPING é o caminho vanilla
                    original_internal_path = TEXTURE_MAPPING[item_type]['paths'][0]
                    selected_textures[item_type] = {
                        'pack_id': 'default', # Indica que é vanilla
                        'original_internal_path': original_internal_path # Caminho dentro do ZIP vanilla
                    }
                else:
                    # Encontra o pack e a textura correspondente
                    pack_data = next((p for p in session.get('uploaded_packs_data', []) if p['id'] == selected_pack_id), None)
                    if pack_data and item_type in pack_data['available_textures']:
                        selected_textures[item_type] = {
                            'pack_id': selected_pack_id,
                            'original_internal_path': pack_data['available_textures'][item_type]['original_internal_path']
                        }
                    else:
                        print(f"AVISO: Textura para '{item_type}' do pack '{selected_pack_id}' não encontrada. Usando default.")
                        # Fallback para vanilla se a textura selecionada não for encontrada no pack
                        original_internal_path = TEXTURE_MAPPING[item_type]['paths'][0]
                        selected_textures[item_type] = {
                            'pack_id': 'default',
                            'original_internal_path': original_internal_path
                        }
            else:
                print(f"AVISO: Tipo de item '{item_type}' não reconhecido no TEXTURE_MAPPING.")

    # Cria um novo ZIP para o pack combinado
    combined_pack_id = str(uuid.uuid4())
    combined_pack_name = f"Combined_Pack_{combined_pack_id}.zip"
    combined_pack_path = os.path.join(app.config['GENERATED_PACKS_FOLDER'], combined_pack_name)

    try:
        with zipfile.ZipFile(combined_pack_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
            # Adiciona o pack.mcmeta para o novo pack
            new_zip.writestr('pack.mcmeta', json.dumps({
                "pack": {
                    "pack_format": 15, # Ajuste conforme a versão do Minecraft (ex: 15 para 1.20.x)
                    "description": "Pack de Texturas Combinado pelo Mixer"
                }
            }, indent=4))

            # Adiciona a skin padrão se fornecida
            if default_skin_path:
                # Caminho da skin vanilla dentro do JAR/ZIP
                vanilla_skin_path_in_zip = f"assets/minecraft/textures/entity/{default_skin_path}"
                
                # Caminho da skin padrão dentro do novo pack
                dest_skin_path = f"assets/minecraft/textures/entity/{default_skin_path}"
                
                # Tenta copiar do vanilla_previews se for steve.png ou alex.png
                vanilla_skin_source_path = os.path.join(app.config['APP_ROOT'], 'static', 'vanilla_previews', default_skin_path)
                if os.path.exists(vanilla_skin_source_path):
                    # Adiciona a skin ao novo pack
                    with open(vanilla_skin_source_path, 'rb') as f_skin:
                        new_zip.writestr(dest_skin_path, f_skin.read())
                    print(f"Skin padrão '{default_skin_path}' adicionada ao pack combinado.")
                else:
                    print(f"AVISO: Skin padrão '{default_skin_path}' não encontrada em vanilla_previews. Não será adicionada.")

            # Copia as texturas selecionadas para o novo ZIP
            for item_type, texture_info in selected_textures.items():
                pack_id = texture_info['pack_id']
                original_internal_path = texture_info['original_internal_path']

                if pack_id == 'default':
                    # Para texturas vanilla, precisamos copiá-las de algum lugar.
                    # Primeiro, tenta do default.zip se disponível
                    default_zip_path = os.path.join(app.config['APP_ROOT'], 'default.zip')
                    if os.path.exists(default_zip_path):
                        try:
                            with zipfile.ZipFile(default_zip_path, 'r') as default_zip:
                                if original_internal_path in default_zip.namelist():
                                    with default_zip.open(original_internal_path) as source_file:
                                        new_zip.writestr(original_internal_path, source_file.read())
                                    print(f"Adicionado '{item_type}' do default.zip para o pack combinado.")
                                    continue
                        except Exception as e:
                            print(f"Erro ao ler do default.zip: {e}")
                            traceback.print_exc()
                    
                    # Fallback para vanilla_previews
                    vanilla_filename = os.path.basename(original_internal_path)
                    source_path = os.path.join(app.config['APP_ROOT'], 'static', 'vanilla_previews', vanilla_filename)
                    
                    # Se for um ícone recortado (coração/fome), o nome do arquivo em vanilla_previews
                    # será diferente do original_internal_path (gui/icons.png).
                    # Precisamos mapear para o nome do arquivo recortado.
                    if item_type == "Ícone de Coração":
                        source_path = os.path.join(app.config['APP_ROOT'], 'static', 'vanilla_previews', 'heart_full.png')
                    elif item_type == "Ícone de Comida":
                        source_path = os.path.join(app.config['APP_ROOT'], 'static', 'vanilla_previews', 'hunger_full.png')
                    elif item_type == "Esfera de Fogo" and "fireball.gif" in VANILLA_PREVIEW_MAP_PYTHON.get(item_type, ""):
                        source_path = os.path.join(app.config['APP_ROOT'], 'static', 'vanilla_previews', 'fireball.gif')
                        original_internal_path = original_internal_path.replace('.png', '.gif') # Mudar destino para gif
                    
                    if os.path.exists(source_path):
                        with open(source_path, 'rb') as f_src:
                            # O destino no novo ZIP deve ser o caminho original (assets/minecraft/textures/...)
                            new_zip.writestr(f"assets/minecraft/textures/{original_internal_path}", f_src.read())
                        print(f"Adicionado vanilla '{item_type}' de '{source_path}' para o pack combinado.")
                    else:
                        print(f"AVISO: Textura vanilla para '{item_type}' não encontrada em '{source_path}'. Pulando.")
                else:
                    # Para texturas de packs enviados, copiamos do ZIP original
                    pack_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{pack_id}.zip")
                    if os.path.exists(pack_filepath):
                        with zipfile.ZipFile(pack_filepath, 'r') as original_zip:
                            if original_internal_path in original_zip.namelist():
                                with original_zip.open(original_internal_path) as source_file:
                                    # Adiciona a textura ao novo pack
                                    new_zip.writestr(original_internal_path, source_file.read())
                                print(f"Adicionado '{item_type}' de pack '{pack_id}' para o pack combinado.")
                            else:
                                print(f"AVISO: Textura interna '{original_internal_path}' não encontrada no pack '{pack_id}'. Pulando.")
                    else:
                        print(f"AVISO: Arquivo ZIP do pack '{pack_id}' não encontrado. Pulando textura para '{item_type}'.")

        print(f"Pack combinado gerado com sucesso: {combined_pack_name}")
        print(f"Total de texturas incluídas: {len(selected_textures)}")

    except Exception as e:
        print(f"ERRO ao gerar o pack combinado: {e}")
        traceback.print_exc()
        return render_template('selection.html', 
                               uploaded_packs_data=session.get('uploaded_packs_data', []),
                               profiles=PROFILES,
                               all_item_types=sorted(list(TEXTURE_MAPPING.keys())), # Fallback para todos os tipos
                               vanilla_preview_map_json_string=json.dumps(VANILLA_PREVIEW_MAP_PYTHON),
                               error="Erro ao gerar o pack. Por favor, tente novamente.")

    return redirect(url_for('download_pack_page', pack_name=combined_pack_name))

@app.route('/download_pack_page/<pack_name>')
def download_pack_page(pack_name):
    return render_template('download.html', pack_name=pack_name)

@app.route('/download/<pack_name>')
def download_pack(pack_name):
    return send_from_directory(app.config['GENERATED_PACKS_FOLDER'], pack_name, as_attachment=True)

# --- Configura a rota estática para a pasta de previews ---
app.add_url_rule(
    '/temp_previews/<path:filename>',
    endpoint='temp_previews',
    view_func=lambda filename: send_from_directory(app.config['TEMP_PREVIEW_FOLDER'], filename)
)

if __name__ == '__main__':
    with app.app_context():
        # Inicializa o mapa de previews vanilla
        initialize_vanilla_preview_map()
        # Carrega as texturas do default.zip
        load_default_zip_textures(app.config['APP_ROOT'])
        print("Aplicação inicializada com sucesso!")

    app.run(debug=True, host='0.0.0.0')

