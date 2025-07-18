import os
import zipfile
import json
import shutil
import uuid
import re
import traceback
from PIL import Image, ImageSequence, ImageDraw
from flask import url_for

# --- Mapeamento de Caminhos de Textura para Nomes Amigáveis ---
TEXTURE_MAPPING = {
    # Blocos Comuns
    "Lã": {"paths": [
        "block/white_wool.png", "blocks/white_wool.png", # Singular e plural
        "block/orange_wool.png", "blocks/orange_wool.png",
        "block/magenta_wool.png", "blocks/magenta_wool.png",
        "block/light_blue_wool.png", "blocks/light_blue_wool.png",
        "block/yellow_wool.png", "blocks/yellow_wool.png",
        "block/lime_wool.png", "blocks/lime_wool.png",
        "block/pink_wool.png", "blocks/pink_wool.png",
        "block/gray_wool.png", "blocks/gray_wool.png",
        "block/light_gray_wool.png", "blocks/light_gray_wool.png",
        "block/cyan_wool.png", "blocks/cyan_wool.png",
        "block/purple_wool.png", "blocks/purple_wool.png",
        "block/blue_wool.png", "blocks/blue_wool.png",
        "block/brown_wool.png", "blocks/brown_wool.png",
        "block/green_wool.png", "blocks/green_wool.png",
        "block/red_wool.png", "blocks/red_wool.png",
        "block/black_wool.png", "blocks/black_wool.png",
        # Adicionado nome alternativo para lã
        "block/wool_colored_white.png", "blocks/wool_colored_white.png",
        "block/wool_colored_orange.png", "blocks/wool_colored_orange.png",
        "block/wool_colored_magenta.png", "blocks/wool_colored_magenta.png",
        "block/wool_colored_light_blue.png", "blocks/wool_colored_light_blue.png",
        "block/wool_colored_yellow.png", "blocks/wool_colored_yellow.png",
        "block/wool_colored_lime.png", "blocks/wool_colored_lime.png",
        "block/wool_colored_pink.png", "blocks/wool_colored_pink.png",
        "block/wool_colored_gray.png", "blocks/wool_colored_gray.png",
        "block/wool_colored_light_gray.png", "blocks/wool_colored_light_gray.png",
        "block/wool_colored_cyan.png", "blocks/wool_colored_cyan.png",
        "block/wool_colored_purple.png", "blocks/wool_colored_purple.png",
        "block/wool_colored_blue.png", "blocks/wool_colored_blue.png",
        "block/wool_colored_brown.png", "blocks/wool_colored_brown.png",
        "block/wool_colored_green.png", "blocks/wool_colored_green.png",
        "block/wool_colored_red.png", "blocks/wool_colored_red.png",
        "block/wool_colored_black.png", "blocks/wool_colored_black.png",
    ]},
    "Madeira (Tábuas)": {"paths": [
        "block/oak_planks.png", "blocks/oak_planks.png",
        "block/spruce_planks.png", "blocks/spruce_planks.png",
        "block/birch_planks.png", "blocks/birch_planks.png",
        "block/jungle_planks.png", "blocks/jungle_planks.png",
        "block/acacia_planks.png", "blocks/acacia_planks.png",
        "block/dark_oak_planks.png", "blocks/dark_oak_planks.png",
        "block/crimson_planks.png", "blocks/crimson_planks.png",
        "block/warped_planks.png", "blocks/warped_planks.png"
    ]},
    "Pedra": {"paths": ["block/stone.png", "blocks/stone.png", "block/cobblestone.png", "blocks/cobblestone.png", "block/mossy_cobblestone.png", "blocks/mossy_cobblestone.png"]},
    "Minério de Diamante": {"paths": ["block/diamond_ore.png", "blocks/diamond_ore.png"]},
    "Minério de Esmeralda": {"paths": ["block/emerald_ore.png", "blocks/emerald_ore.png"]},
    "Esmeralda (Item)": {"paths": ["item/emerald.png", "items/emerald.png"]},

    # Espadas
    "Espada de Diamante": {"paths": ["item/diamond_sword.png", "items/diamond_sword.png"]},
    "Espada de Ferro": {"paths": ["item/iron_sword.png", "items/iron_sword.png"]},
    "Espada de Ouro": {"paths": ["item/gold_sword.png", "items/gold_sword.png", "item/golden_sword.png", "items/golden_sword.png"]},
    "Espada de Madeira": {"paths": ["item/wood_sword.png", "items/wood_sword.png", "item/wooden_sword.png", "items/wooden_sword.png"]},
    "Espada de Pedra": {"paths": ["item/stone_sword.png", "items/stone_sword.png"]},

    # Picaretas
    "Picareta de Diamante": {"paths": ["item/diamond_pickaxe.png", "items/diamond_pickaxe.png"]},
    "Picareta de Ferro": {"paths": ["item/iron_pickaxe.png", "items/iron_pickaxe.png"]},
    "Picareta de Ouro": {"paths": ["item/gold_pickaxe.png", "items/gold_pickaxe.png", "item/golden_pickaxe.png", "items/golden_pickaxe.png"]},
    "Picareta de Madeira": {"paths": ["item/wood_pickaxe.png", "items/wood_pickaxe.png", "item/wooden_pickaxe.png", "items/wooden_pickaxe.png"]},
    "Picareta de Pedra": {"paths": ["item/stone_pickaxe.png", "items/stone_pickaxe.png"]},

    # Machados
    "Machado de Diamante": {"paths": ["item/diamond_axe.png", "items/diamond_axe.png"]},
    "Machado de Ferro": {"paths": ["item/iron_axe.png", "items/iron_axe.png"]},
    "Machado de Ouro": {"paths": ["item/gold_axe.png", "items/gold_axe.png", "item/golden_axe.png", "items/golden_axe.png"]},
    "Machado de Madeira": {"paths": ["item/wood_axe.png", "items/wood_axe.png", "item/wooden_axe.png", "items/wooden_axe.png"]},
    "Machado de Pedra": {"paths": ["item/stone_axe.png", "items/stone_axe.png"]},

    # Pás
    "Pá de Diamante": {"paths": ["item/diamond_shovel.png", "items/diamond_shovel.png"]},
    "Pá de Ferro": {"paths": ["item/iron_shovel.png", "items/iron_shovel.png"]},
    "Pá de Ouro": {"paths": ["item/gold_shovel.png", "items/gold_shovel.png", "item/golden_shovel.png", "items/golden_shovel.png"]},
    "Pá de Madeira": {"paths": ["item/wood_shovel.png", "items/wood_shovel.png", "item/wooden_shovel.png", "items/wooden_shovel.png"]},
    "Pá de Pedra": {"paths": ["item/stone_shovel.png", "items/stone_shovel.png"]},

    # Enxadas
    "Enxada de Diamante": {"paths": ["item/diamond_hoe.png", "items/diamond_hoe.png"]},
    "Enxada de Ferro": {"paths": ["item/iron_hoe.png", "items/iron_hoe.png"]},
    "Enxada de Ouro": {"paths": ["item/gold_hoe.png", "items/gold_hoe.png", "item/golden_hoe.png", "items/golden_hoe.png"]},
    "Enxada de Madeira": {"paths": ["item/wood_hoe.png", "items/wood_hoe.png", "item/wooden_hoe.png", "items/wooden_hoe.png"]},
    "Enxada de Pedra": {"paths": ["item/stone_hoe.png", "items/stone_hoe.png"]},

    # Armaduras de Diamante
    "Capacete de Diamante": {"paths": ["item/diamond_helmet.png", "items/diamond_helmet.png"]},
    "Peitoral de Diamante": {"paths": ["item/diamond_chestplate.png", "items/diamond_chestplate.png"]},
    "Calças de Diamante": {"paths": ["item/diamond_leggings.png", "items/diamond_leggings.png"]},
    "Botas de Diamante": {"paths": ["item/diamond_boots.png", "items/diamond_boots.png"]},

    # Armaduras de Ferro
    "Capacete de Ferro": {"paths": ["item/iron_helmet.png", "items/iron_helmet.png"]},
    "Peitoral de Ferro": {"paths": ["item/iron_chestplate.png", "items/iron_chestplate.png"]},
    "Calças de Ferro": {"paths": ["item/iron_leggings.png", "items/iron_leggings.png"]},
    "Botas de Ferro": {"paths": ["item/iron_boots.png", "items/iron_boots.png"]},

    # Armaduras de Ouro
    "Capacete de Ouro": {"paths": ["item/gold_helmet.png", "items/gold_helmet.png", "item/golden_helmet.png", "items/golden_helmet.png"]},
    "Peitoral de Ouro": {"paths": ["item/gold_chestplate.png", "items/gold_chestplate.png", "item/golden_chestplate.png", "items/golden_chestplate.png"]},
    "Calças de Ouro": {"paths": ["item/gold_leggings.png", "items/gold_leggings.png", "item/golden_leggings.png", "items/golden_leggings.png"]},
    "Botas de Ouro": {"paths": ["item/gold_boots.png", "items/gold_boots.png", "item/golden_boots.png", "items/golden_boots.png"]},

    # Armaduras de Couro (com e sem overlay)
    "Capacete de Couro": {"paths": ["item/leather_helmet.png", "items/leather_helmet.png", "item/leather_helmet_overlay.png", "items/leather_helmet_overlay.png"]},
    "Peitoral de Couro": {"paths": ["item/leather_chestplate.png", "items/leather_chestplate.png", "item/leather_chestplate_overlay.png", "items/leather_chestplate_overlay.png"]},
    "Calças de Couro": {"paths": ["item/leather_leggings.png", "items/leather_leggings.png", "item/leather_leggings_overlay.png", "items/leather_leggings_overlay.png"]},
    "Botas de Couro": {"paths": ["item/leather_boots.png", "items/leather_boots.png", "item/leather_boots_overlay.png", "items/leather_boots_overlay.png"]},

    # Itens Específicos
    "Arco": {"paths": ["item/bow_pulling_0.png", "items/bow_pulling_0.png", "item/bow_pulling_1.png", "items/bow_pulling_1.png", "item/bow_pulling_2.png", "items/bow_pulling_2.png", "item/bow_standby.png", "items/bow_standby.png"]},
    "Flecha": {"paths": ["item/arrow.png", "items/arrow.png"]},
    "Esfera de Fogo": {"paths": ["item/fireball.png", "items/fireball.png", "entity/fireball.png", "textures/entity/fireball.png"], "is_animated": True}, 
    "Creme de Magma": {"paths": ["item/magma_cream.png", "items/magma_cream.png"]},
    "Olho do Fim": {"paths": ["item/ender_eye.png", "items/ender_eye.png"]},
    "Garrafa de XP": {"paths": ["item/experience_bottle.png", "items/experience_bottle.png"]},
    "Pó de Glowstone": {"paths": ["item/glowstone_dust.png", "items/glowstone_dust.png"]},
    "Maçã Dourada": {"paths": ["item/golden_apple.png", "items/golden_apple.png", "item/apple_golden.png", "items/apple_golden.png"]},
    "Tesoura": {"paths": ["item/shears.png", "items/shears.png"]},
    "Mapa Vazio": {"paths": ["item/map_empty.png", "items/map_empty.png"]},
    "Mapa Preenchido": {"paths": ["item/map_filled.png", "items/map_filled.png"]},

    # Ícones GUI (requerem recorte)
    "Ícone de Coração": {"paths": ["gui/icons.png"], "is_icon_sprite": True, "icon_type": "heart_full"},
    "Ícone de Comida": {"paths": ["gui/icons.png"], "is_icon_sprite": True, "icon_type": "hunger_full"},
}

# --- Definição dos Perfis ---
PROFILES = {
    "bedwars": { # Agora o perfil padrão
        "name": "Bedwars",
        "items": [
            "Lã", "Espada de Diamante", "Arco", "Flecha", "Esfera de Fogo", "Creme de Magma",
            "Ícone de Coração", "Ícone de Comida", # Adicionados aqui
            "Picareta de Ferro", "Picareta de Diamante", "Machado de Ferro", "Machado de Diamante",
            "Madeira (Tábuas)", "Pedra", # Adicionados para Bedwars
        ]
    },
    "pvp": {
        "name": "PvP",
        "items": [
            "Espada de Diamante", "Espada de Ferro", "Espada de Ouro", "Espada de Madeira", "Espada de Pedra",
            "Capacete de Diamante", "Peitoral de Diamante", "Calças de Diamante", "Botas de Diamante",
            "Capacete de Ferro", "Peitoral de Ferro", "Calças de Ferro", "Botas de Ferro",
            "Ícone de Coração", "Ícone de Comida", # HUD de vida e fome
            "Lã", # Lã ainda pode ser relevante para alguns PvPs
            "Madeira (Tábuas)",
        ]
    },
    "standard": {
        "name": "Padrão",
        "items": [
            "Lã", "Madeira (Tábuas)", "Pedra", "Minério de Diamante", "Minério de Esmeralda",
            "Espada de Diamante", "Arco", "Flecha", "Picareta de Ferro", "Picareta de Diamante",
            "Ícone de Coração", "Ícone de Comida",
        ]
    }
}

# Variável global para o mapa de previews vanilla
VANILLA_PREVIEW_MAP_PYTHON = {}

# --- Sistema de Default.zip ---
DEFAULT_ZIP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "default.zip")  # Caminho para o default.zip no servidor
DEFAULT_TEXTURES_CACHE = {}  # Cache das texturas do default.zip
_default_zip_loaded = False

# Função para converter códigos de cor do Minecraft (&x ou §x) para HTML/CSS
def format_minecraft_text(text):
    color_map = {
        "0": "#000000", # Black
        "1": "#0000AA", # Dark Blue
        "2": "#00AA00", # Dark Green
        "3": "#00AAAA", # Dark Aqua
        "4": "#AA0000", # Dark Red
        "5": "#AA00AA", # Dark Purple
        "6": "#FFAA00", # Gold
        "7": "#AAAAAA", # Gray
        "8": "#555555", # Dark Gray
        "9": "#5555FF", # Blue
        "a": "#55FF55", # Green
        "b": "#55FFFF", # Aqua
        "c": "#FF5555", # Red
        "d": "#FF55FF", # Light Purple
        "e": "#FFFF55", # Yellow
        "f": "#FFFFFF", # White
    }
    
    style_map = {
        "l": "font-weight: bold;",
        "m": "text-decoration: line-through;",
        "n": "text-decoration: underline;",
        "o": "font-style: italic;",
        "k": "text-transform: uppercase;",
        "r": "color: #FFFFFF; font-weight: normal; text-decoration: none; font-style: normal;",
    }

    def replace_code(match):
        code = match.group(1).lower()
        if code in color_map:
            return f"<span style=\"color: {color_map[code]};\">"
        elif code in style_map:
            return f"<span style=\"{style_map[code]}\">"
        return match.group(0)

    formatted_text = re.sub(r"[&§]([0-9a-fk-or])", replace_code, text)
    open_spans = formatted_text.count("<span")
    close_spans = formatted_text.count("</span>")
    formatted_text += "</span>" * (open_spans - close_spans)

    return formatted_text


# Função para recortar ícones de coração e fome do sprite sheet icons.png
def crop_heart_hunger_smart(icons_png_path, icon_type, pack_preview_dir, pack_upload_id):
    """
    Recorta ícones específicos do sprite sheet icons.png
    
    Args:
        icons_png_path: Caminho para o arquivo icons.png
        icon_type: Tipo do ícone ("heart_full", "hunger_full", etc.)
        pack_preview_dir: Diretório onde salvar o ícone recortado
        pack_upload_id: ID do pack para nomear o arquivo
    
    Returns:
        URL do ícone recortado ou None se falhar
    """
    try:
        # Coordenadas dos ícones no sprite sheet icons.png (256x256)
        # Estas coordenadas são baseadas no layout padrão do Minecraft
        icon_coords = {
            "heart_full": (52, 0, 61, 9),      # Coração cheio
            "heart_half": (61, 0, 70, 9),      # Meio coração
            "heart_empty": (16, 0, 25, 9),     # Coração vazio
            "hunger_full": (52, 27, 61, 36),   # Fome cheia
            "hunger_half": (61, 27, 70, 36),   # Meia fome
            "hunger_empty": (16, 27, 25, 36),  # Fome vazia
        }
        
        if icon_type not in icon_coords:
            print(f"Tipo de ícone \'{icon_type}\' não suportado")
            return None
            
        # Abre a imagem icons.png
        with Image.open(icons_png_path) as img:
            # Converte para RGBA para garantir compatibilidade
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            # Recorta o ícone usando as coordenadas
            left, top, right, bottom = icon_coords[icon_type]
            cropped_icon = img.crop((left, top, right, bottom))
            
            # Redimensiona para um tamanho maior para melhor visualização (opcional)
            cropped_icon = cropped_icon.resize((18, 18), Image.NEAREST)
            
            # Salva o ícone recortado
            output_filename = f"{pack_upload_id}_{icon_type}.png"
            output_path = os.path.join(pack_preview_dir, output_filename)
            cropped_icon.save(output_path)
            
            # Retorna a URL para o ícone recortado
            return url_for("temp_previews", filename=f"{pack_upload_id}/{output_filename}")
            
    except Exception as e:
        print(f"Erro ao recortar ícone {icon_type}: {e}")
        return None

# Função para gerar GIF animado a partir de PNG e arquivo .mcmeta
def generate_animated_gif(png_path, mcmeta_path, output_path):
    """
    Gera um GIF animado a partir de um PNG com frames verticais e arquivo .mcmeta
    
    Args:
        png_path: Caminho para o arquivo PNG com frames
        mcmeta_path: Caminho para o arquivo .mcmeta com informações de animação
        output_path: Caminho onde salvar o GIF gerado
    
    Returns:
        Caminho do GIF gerado ou None se falhar
    """
    try:
        # Lê o arquivo .mcmeta para obter informações de animação
        with open(mcmeta_path, "r") as f:
            mcmeta_data = json.load(f)
        
        animation_info = mcmeta_data.get("animation", {})
        frame_time = animation_info.get("frametime", 1)  # Tempo por frame em ticks (1 tick = 1/20 segundo)
        interpolate = animation_info.get("interpolate", False)
        frames_info = animation_info.get("frames", [])
        
        # Abre a imagem PNG
        with Image.open(png_path) as img:
            # Converte para RGBA para garantir compatibilidade
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            width, height = img.size
            
            # Calcula o tamanho de cada frame (assumindo que são quadrados)
            frame_size = width
            num_frames = height // frame_size
            
            # Se não há informação específica de frames, usa todos os frames disponíveis
            if not frames_info:
                frames_info = list(range(num_frames))
            
            # Extrai os frames
            frames = []
            for i, frame_info in enumerate(frames_info):
                if isinstance(frame_info, dict):
                    frame_index = frame_info.get("index", i)
                    frame_duration = frame_info.get("time", frame_time)
                else:
                    frame_index = frame_info
                    frame_duration = frame_time
                
                # Recorta o frame da imagem
                top = frame_index * frame_size
                bottom = top + frame_size
                frame = img.crop((0, top, width, bottom))
                
                # Converte o tempo de ticks para milissegundos (1 tick = 50ms)
                duration_ms = int(frame_duration * 50)
                
                frames.append((frame, duration_ms))
            
            # Salva como GIF animado
            if frames:
                first_frame = frames[0][0]
                other_frames = [frame[0] for frame in frames[1:]]
                durations = [frame[1] for frame in frames]
                
                first_frame.save(
                    output_path,
                    save_all=True,
                    append_images=other_frames,
                    duration=durations,
                    loop=0,  # Loop infinito
                    optimize=True
                )
                print(f"[DEBUG GIF] GIF salvo em: {output_path}")
                return output_path
            
    except Exception as e:
        print(f"[DEBUG GIF] Erro ao gerar GIF animado para {png_path}: {e}")
        return None

def load_default_zip_textures(app_root_path):
    """
    Carrega e cacheia as texturas do default.zip na inicialização da aplicação
    
    Args:
        app_root_path: Caminho raiz da aplicação Flask
    
    Returns:
        True se carregou com sucesso, False caso contrário
    """
    global DEFAULT_TEXTURES_CACHE, _default_zip_loaded
    
    if _default_zip_loaded:
        return True
    
    default_zip_full_path = DEFAULT_ZIP_PATH # Já é o caminho completo
    
    if not os.path.exists(default_zip_full_path):
        print(f"AVISO: default.zip não encontrado em {default_zip_full_path}")
        return False
    
    print(f"Carregando texturas do default.zip: {default_zip_full_path}")
    
    try:
        with zipfile.ZipFile(default_zip_full_path, "r") as default_zf:
            all_members = default_zf.namelist()
            
            # Processa cada textura mapeada
            for friendly_name, item_info in TEXTURE_MAPPING.items():
                # Procura por qualquer um dos caminhos possíveis para esta textura
                for texture_path in item_info["paths"]:
                    # Garante que o caminho interno do ZIP comece com "assets/minecraft/textures/"
                    # e remova qualquer prefixo duplicado
                    if texture_path.startswith("assets/minecraft/textures/"):
                        full_path = texture_path
                    elif texture_path.startswith("item/") or texture_path.startswith("items/") or \
                         texture_path.startswith("block/") or texture_path.startswith("blocks/") or \
                         texture_path.startswith("gui/") or texture_path.startswith("entity/") or texture_path.startswith("textures/entity/"):
                        full_path = f"assets/minecraft/textures/{texture_path}"
                    else:
                        # Caso não tenha prefixo, assume que é um caminho direto dentro de textures/
                        full_path = f"assets/minecraft/textures/{texture_path}"

                    if full_path in all_members:
                        # Lê o conteúdo da textura em memória
                        texture_data = default_zf.read(full_path)
                        
                        DEFAULT_TEXTURES_CACHE[friendly_name] = {
                            "data": texture_data,
                            "internal_path": full_path,
                            "original_filename": os.path.basename(texture_path)
                        }
                        
                        print(f"  -> Carregada textura padrão: {friendly_name}")
                        break  # Encontrou uma textura para este friendly_name
            
            # Processa icons.png se existir
            icons_path = "assets/minecraft/textures/gui/icons.png"
            if icons_path in all_members:
                icons_data = default_zf.read(icons_path)
                DEFAULT_TEXTURES_CACHE["_icons_png"] = {
                    "data": icons_data,
                    "internal_path": icons_path,
                    "original_filename": "icons.png"
                }
                print(f"  -> Carregado icons.png padrão")
        
        _default_zip_loaded = True
        print(f"Default.zip carregado com sucesso. {len(DEFAULT_TEXTURES_CACHE)} texturas em cache.")
        return True
        
    except Exception as e:
        print(f"Erro ao carregar default.zip: {e}")
        traceback.print_exc()
        return False

def get_default_texture_for_pack(friendly_name, pack_preview_dir, pack_upload_id):
    """
    Obtém uma textura padrão do cache do default.zip para um pack específico
    
    Args:
        friendly_name: Nome amigável da textura
        pack_preview_dir: Diretório de preview do pack
        pack_upload_id: ID do pack
    
    Returns:
        Dicionário com informações da textura ou None se não encontrada
    """
    if friendly_name not in DEFAULT_TEXTURES_CACHE:
        return None
    
    try:
        texture_info = DEFAULT_TEXTURES_CACHE[friendly_name]
        
        # Salva a textura no diretório de preview do pack
        preview_filename = f"default_{texture_info['original_filename']}"
        preview_dest_path = os.path.join(pack_preview_dir, preview_filename)
        
        with open(preview_dest_path, "wb") as dest:
            dest.write(texture_info["data"])
                
        final_filename = os.path.basename(preview_dest_path)
        print('476: ', final_filename)
        return {
            "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{final_filename.replace("\\", "/")}"),
            "original_internal_path": texture_info["internal_path"],
            "is_default": True
        }
        
    except Exception as e:
        print(f"Erro ao obter textura padrão para {friendly_name}: {e}")
        traceback.print_exc()
        return None

def get_default_icons_for_pack(pack_preview_dir, pack_upload_id):
    """
    Processa ícones do default.zip para um pack específico
    
    Args:
        pack_preview_dir: Diretório de preview do pack
        pack_upload_id: ID do pack
    
    Returns:
        Dicionário com ícones processados
    """
    if "_icons_png" not in DEFAULT_TEXTURES_CACHE:
        return {}
    
    try:
        icons_info = DEFAULT_TEXTURES_CACHE["_icons_png"]
        
        # Salva o icons.png temporariamente
        temp_icons_path = os.path.join(pack_preview_dir, f"default_icons_source.png")
        with open(temp_icons_path, "wb") as dest:
            dest.write(icons_info["data"])
        
        # Processa os ícones
        processed_icons = {}
        for friendly_name, item_info in TEXTURE_MAPPING.items():
            if item_info.get("is_icon_sprite") and item_info.get("icon_type"):
                cropped_url = crop_heart_hunger_smart(
                    temp_icons_path,
                    item_info["icon_type"],
                    pack_preview_dir,
                    f"default_{pack_upload_id}"
                )
                if cropped_url:
                    # Adiciona borda vermelha ao ícone padrão
                    icon_filename = cropped_url.split("/")[-1]
                    icon_path = os.path.join(pack_preview_dir, icon_filename)
                    
                    if os.path.exists(icon_path):                       
                        processed_icons[friendly_name] = {
                            "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{icon_filename.replace("\\", "/")}"),
                            "original_internal_path": icons_info["internal_path"],
                            "is_default": True
                        }
        
        # Remove o arquivo temporário
        if os.path.exists(temp_icons_path):
            os.remove(temp_icons_path)
        
        return processed_icons
        
    except Exception as e:
        print(f"Erro ao processar ícones padrão: {e}")
        traceback.print_exc()
        return {}

# --- Função para analisar um Resource Pack (VERSÃO CORRIGIDA COM PRIORIDADE) ---
def analyze_resource_pack(zip_path, pack_upload_id, temp_preview_folder):
    """
    Analisa um resource pack e extrai as texturas disponíveis
    VERSÃO CORRIGIDA: Prioriza texturas do usuário sobre as padrão
    
    Args:
        zip_path: Caminho para o arquivo ZIP do resource pack
        pack_upload_id: ID único para este pack
        temp_preview_folder: Pasta onde salvar os previews temporários
    
    Returns:
        Dicionário com informações do pack ou None se falhar
    """
    pack_name = os.path.basename(zip_path).replace(".zip", "")
    user_textures = {}  # Texturas encontradas no pack do usuário

    pack_preview_dir = os.path.join(temp_preview_folder, pack_upload_id)
    os.makedirs(pack_preview_dir, exist_ok=True)

    print(f"\n--- Iniciando análise para pack: {zip_path} (ID: {pack_upload_id}) ---")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Tenta ler pack.mcmeta para um nome mais amigável
            try:
                with zf.open("pack.mcmeta") as mcmeta_file:
                    mcmeta_content = json.loads(mcmeta_file.read().decode("utf-8"))
                    if "pack" in mcmeta_content and "description" in mcmeta_content["pack"]:
                        desc = mcmeta_content["pack"]["description"]
                        # Se a descrição for um objeto JSON com texto e formatação, extraia o texto
                        if isinstance(desc, dict) and "text" in desc:
                            pack_name = desc["text"].strip()
                        elif isinstance(desc, str):
                            pack_name = desc.strip()
                        # Formata o nome do pack com cores do Minecraft
                        pack_name = format_minecraft_text(pack_name)
            except (KeyError, json.JSONDecodeError, zipfile.BadZipFile):
                print(f"pack.mcmeta não encontrado ou inválido para {zip_path}. Usando nome do arquivo: {pack_name}")
                pass

            all_zip_members = zf.namelist()

            # Processa icons.png primeiro se existir
            icons_png_path = "assets/minecraft/textures/gui/icons.png"
            if icons_png_path in all_zip_members:
                print(f"Detectado {icons_png_path}. Processando ícones de sprite sheet.")
                temp_icons_path = os.path.join(pack_preview_dir, f"{pack_upload_id}_icons_source.png")
                with zf.open(icons_png_path) as source, open(temp_icons_path, "wb") as dest:
                    shutil.copyfileobj(source, dest)
                
                for friendly_name, item_info in TEXTURE_MAPPING.items():
                    if item_info.get("is_icon_sprite") and item_info.get("icon_type"):
                        # Verifica se o icons.png do pack do usuário é o que estamos procurando
                        # Isso evita processar icons.png de outros lugares ou se o mapeamento estiver errado
                        if icons_png_path in item_info["paths"]:
                            print(f"Tentando recortar {friendly_name} (tipo: {item_info['icon_type']}) de {icons_png_path}")
                            cropped_url = crop_heart_hunger_smart(
                                temp_icons_path,
                                item_info["icon_type"],
                                pack_preview_dir,
                                pack_upload_id
                            )
                            if cropped_url:
                                # Adiciona borda verde para indicar que é textura do usuário
                                icon_filename = cropped_url.split("/")[-1]
                                icon_path = os.path.join(pack_preview_dir, icon_filename)
                                
                                if os.path.exists(icon_path):
                                    print('612: ', icon_filename)
                                    user_textures[friendly_name] = {
                                        "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{icon_filename.replace("\\", "/")}"),
                                        "original_internal_path": icons_png_path,
                                        "is_default": False
                                    }
                                    print(f"  -> Recorte de {friendly_name} SUCESSO. URL: {user_textures[friendly_name]['static_url_path']}")
                            else:
                                print(f"  -> Recorte de {friendly_name} FALHA.")

            # Itera sobre os arquivos restantes do ZIP para outras texturas
            for member_path in all_zip_members:
                # Apenas processa arquivos PNG dentro de assets/minecraft/textures/
                if member_path.startswith("assets/minecraft/textures/") and member_path.endswith(".png"):
                    # Remove "assets/minecraft/textures/" do início para obter o caminho relativo
                    relative_texture_path = member_path[len("assets/minecraft/textures/"):]

                    found_friendly_name = False
                    for friendly_name, item_info in TEXTURE_MAPPING.items():
                        if relative_texture_path in item_info["paths"] and not item_info.get("is_icon_sprite"):
                            if friendly_name in user_textures:
                                continue 

                            # --- Lógica para Texturas Animadas (com .mcmeta) ---
                            if item_info.get("is_animated"):
                                mcmeta_member_path = member_path + ".mcmeta"
                                if mcmeta_member_path in zf.namelist():
                                    
                                    # Extrai PNG e MCMETA para temp_previews para serem processados
                                    temp_png_path = os.path.join(pack_preview_dir, f"{pack_upload_id}_{os.path.basename(member_path)}")
                                    temp_mcmeta_path = os.path.join(pack_preview_dir, f"{pack_upload_id}_{os.path.basename(mcmeta_member_path)}")

                                    with zf.open(member_path) as source_png, open(temp_png_path, "wb") as dest_png:
                                        shutil.copyfileobj(source_png, dest_png)
                                    with zf.open(mcmeta_member_path) as source_mcmeta, open(temp_mcmeta_path, "wb") as dest_mcmeta:
                                        shutil.copyfileobj(source_mcmeta, dest_mcmeta)
                                    
                                    # Gera o GIF
                                    gif_filename = f"{friendly_name}_{os.path.basename(member_path).replace('.png', '.gif')}"
                                    gif_output_path = os.path.join(pack_preview_dir, gif_filename)
                                    
                                    generated_gif_path = generate_animated_gif(temp_png_path, temp_mcmeta_path, gif_output_path)

                                    if generated_gif_path:
                                        user_textures[friendly_name] = {
                                            "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{os.path.basename(generated_gif_path).replace("\\", "/")}"),
                                            "original_internal_path": member_path,
                                            "is_default": False
                                        }
                                    else:
                                        # Fallback para imagem estática se o GIF falhar
                                        original_filename = os.path.basename(relative_texture_path)
                                        preview_dest_path = os.path.join(pack_preview_dir, original_filename)
                                        with zf.open(member_path) as source, open(preview_dest_path, "wb") as dest:
                                            shutil.copyfileobj(source, dest)
                                                                                
                                        user_textures[friendly_name] = {
                                            "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{original_filename.replace("\\", "/")}"),
                                            "original_internal_path": member_path,
                                            "is_default": False
                                        }
                                else:
                                    # Se .mcmeta não existe, trata como estática
                                    original_filename = os.path.basename(relative_texture_path)
                                    preview_dest_path = os.path.join(pack_preview_dir, original_filename)
                                    with zf.open(member_path) as source, open(preview_dest_path, "wb") as dest:
                                        shutil.copyfileobj(source, dest)
                                    
                                    user_textures[friendly_name] = {
                                        "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{original_filename.replace("\\", "/")}"),
                                        "original_internal_path": member_path,
                                        "is_default": False
                                    }
                            
                            # --- Lógica para Texturas Estáticas (sem .mcmeta ou não marcadas como animadas) ---
                            else:
                                original_filename = os.path.basename(relative_texture_path)
                                preview_dest_path = os.path.join(pack_preview_dir, original_filename)

                                with zf.open(member_path) as source, open(preview_dest_path, "wb") as dest:
                                    shutil.copyfileobj(source, dest)

                                user_textures[friendly_name] = {
                                    "static_url_path": url_for("temp_previews", filename=f"{pack_upload_id}/{original_filename.replace("\\", "/")}"),
                                    "original_internal_path": member_path,
                                    "is_default": False
                                }
                            
                            found_friendly_name = True
                            break # Encontrou um mapeamento para este member_path, vai para o próximo arquivo do ZIP

        
    except Exception as e:
        traceback.print_exc()
        if os.path.exists(pack_preview_dir):
            shutil.rmtree(pack_preview_dir)
        return None

    return {
        "id": pack_upload_id,
        "name": pack_name,
        "formatted_name": pack_name, # O nome já formatado com cores
        "available_textures": user_textures  # Apenas texturas do usuário por enquanto
    }

def analyze_resource_pack_with_defaults(zip_path, pack_upload_id, temp_preview_folder, app_root_path):
    """
    Versão melhorada do analyze_resource_pack que usa o sistema de default.zip
    CORRIGIDA: Prioriza texturas do usuário e adiciona padrão apenas para faltantes
    
    Args:
        zip_path: Caminho para o arquivo ZIP do resource pack
        pack_upload_id: ID único para este pack
        temp_preview_folder: Pasta onde salvar os previews temporários
        app_root_path: Caminho raiz da aplicação Flask
    
    Returns:
        Dicionário com informações do pack ou None se falhar
    """
    # Garante que o default.zip está carregado
    load_default_zip_textures(app_root_path)
    
    # Primeiro, executa a análise normal (apenas texturas do usuário)
    pack_result = analyze_resource_pack(zip_path, pack_upload_id, temp_preview_folder)
    
    if not pack_result:
        return None
    
    user_textures = pack_result["available_textures"]
    pack_preview_dir = os.path.join(temp_preview_folder, pack_upload_id)
    
    # Identifica texturas faltantes (que o usuário não enviou)
    missing_textures = []
    for friendly_name in TEXTURE_MAPPING.keys():
        if friendly_name not in user_textures:
            missing_textures.append(friendly_name)

    
    # Combina texturas do usuário com texturas padrão para faltantes
    final_textures = user_textures.copy()  # Começa com as texturas do usuário

    if missing_textures:        
        # Adiciona texturas padrão para itens faltantes
        for friendly_name in missing_textures:
            default_texture = get_default_texture_for_pack(friendly_name, pack_preview_dir, pack_upload_id)
            if default_texture:
                final_textures[friendly_name] = default_texture
        
        # Processa ícones padrão se necessário
        missing_icons = [name for name in missing_textures if TEXTURE_MAPPING.get(name, {}).get("is_icon_sprite")]
        if missing_icons:
            default_icons = get_default_icons_for_pack(pack_preview_dir, pack_upload_id)
            for friendly_name, icon_info in default_icons.items():
                if friendly_name in missing_textures:
                    final_textures[friendly_name] = icon_info
    
    # Atualiza o resultado com as texturas finais (usuário + padrão para faltantes)
    pack_result["available_textures"] = final_textures

    
    return pack_result

# Inicialização do VANILLA_PREVIEW_MAP_PYTHON
_vanilla_preview_map_initialized = False
def initialize_vanilla_preview_map():
    global VANILLA_PREVIEW_MAP_PYTHON, _vanilla_preview_map_initialized
    if not _vanilla_preview_map_initialized:
        # Mapeia friendly_name para o nome do arquivo PNG/GIF na pasta static/vanilla_previews
        _static_vanilla_map_filenames = {
            "Lã": "white_wool.png",
            "Madeira (Tábuas)": "oak_planks.png",
            "Pedra": "stone.png",
            "Minério de Diamante": "diamond_ore.png",
            "Minério de Esmeralda": "emerald_ore.png",
            "Esmeralda (Item)": "emerald.png",
            "Espada de Diamante": "diamond_sword.png",
            "Espada de Ferro": "iron_sword.png",
            "Espada de Ouro": "gold_sword.png", 
            "Espada de Madeira": "wooden_sword.png",
            "Espada de Pedra": "stone_sword.png",
            "Picareta de Diamante": "diamond_pickaxe.png",
            "Picareta de Ferro": "iron_pickaxe.png",
            "Picareta de Ouro": "golden_pickaxe.png",
            "Picareta de Madeira": "wooden_pickaxe.png",
            "Picareta de Pedra": "stone_pickaxe.png",
            "Machado de Diamante": "diamond_axe.png",
            "Machado de Ferro": "iron_axe.png",
            "Machado de Ouro": "golden_axe.png",
            "Machado de Madeira": "wooden_axe.png",
            "Machado de Pedra": "stone_axe.png",
            "Pá de Diamante": "diamond_shovel.png",
            "Pá de Ferro": "iron_shovel.png",
            "Pá de Ouro": "golden_shovel.png",
            "Pá de Madeira": "wooden_shovel.png",
            "Pá de Pedra": "stone_shovel.png",
            "Enxada de Diamante": "diamond_hoe.png",
            "Enxada de Ferro": "iron_hoe.png",
            "Enxada de Ouro": "golden_hoe.png",
            "Enxada de Madeira": "wooden_hoe.png",
            "Enxada de Pedra": "stone_hoe.png",
            "Capacete de Diamante": "diamond_helmet.png",
            "Peitoral de Diamante": "diamond_chestplate.png",
            "Calças de Diamante": "diamond_leggings.png",
            "Botas de Diamante": "diamond_boots.png",
            "Capacete de Ferro": "iron_helmet.png",
            "Peitoral de Ferro": "iron_chestplate.png",
            "Calças de Ferro": "iron_leggings.png",
            "Botas de Ferro": "iron_boots.png",
            "Capacete de Ouro": "golden_helmet.png",
            "Peitoral de Ouro": "golden_chestplate.png",
            "Calças de Ouro": "golden_leggings.png",
            "Botas de Ouro": "golden_boots.png",
            "Capacete de Couro": "leather_helmet.png",
            "Peitoral de Couro": "leather_chestplate.png",
            "Calças de Couro": "leather_leggings.png",
            "Botas de Couro": "leather_boots.png",
            "Arco": "bow_standby.png",
            "Flecha": "arrow.png",
            "Esfera de Fogo": "fireball.gif", # Agora é um GIF!
            "Creme de Magma": "magma_cream.png",
            "Olho do Fim": "ender_eye.png",
            "Garrafa de XP": "experience_bottle.png",
            "Pó de Glowstone": "glowstone_dust.png",
            "Maçã Dourada": "golden_apple.png",
            "Tesoura": "shears.png",
            "Mapa Vazio": "map_empty.png",
            "Mapa Preenchido": "map_filled.png",
            "Ícone de Coração": "heart_full.png",
            "Ícone de Comida": "hunger_full.png",
            # Adicione mais conforme você tiver os arquivos em static/vanilla_previews
            "Skin Padrão (Steve)": "steve.png", # Adicionado para a skin padrão
            "Skin Padrão (Alex)": "alex.png",   # Adicionado para a skin padrão
        }
        for friendly_name, filename in _static_vanilla_map_filenames.items():
            VANILLA_PREVIEW_MAP_PYTHON[friendly_name] = url_for("static", filename=f"vanilla_previews/{filename}")
        _vanilla_preview_map_initialized = True



