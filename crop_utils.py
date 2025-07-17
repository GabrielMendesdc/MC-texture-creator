from PIL import Image
import os
import json

def detect_texture_resolution(image_path):
    """
    Detecta a resolução da textura baseada no tamanho da imagem.

    Args:
        image_path (str): Caminho para o arquivo icons.png

    Returns:
        int: Resolução da textura (16, 32, 64, etc.)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        # icons.png padrão é 256x256 para 16x, então calculamos a escala
        # Para resoluções maiores (32x, 64x, etc.), a imagem icons.png será maior.
        # Ex: 32x pack: icons.png é 512x512. 64x pack: icons.png é 1024x1024.
        # A base_size de 256 (para 16x) é a referência.
        base_size = 256 # Tamanho de icons.png para um pack 16x
        scale = width // base_size # Calcula a escala (ex: 512 // 256 = 2 para 32x)

        resolution = scale * 16 # Resolução da textura = escala * 16 (ex: 2 * 16 = 32)

        # print(f"Imagem: {width}x{height} -> Textura {resolution}x detectada")
        return resolution
    except Exception as e:
        print(f"Erro ao detectar resolução para {image_path}: {e}")
        return 16  # Padrão fallback se houver erro

def crop_minecraft_icon(image_path, x, y, size, output_path):
    """
    Recorta um ícone específico do arquivo gui/icons.png do Minecraft e salva.

    Args:
        image_path (str): Caminho para o arquivo icons.png
        x (int): Coordenada X do canto superior esquerdo
        y (int): Coordenada Y do canto superior esquerdo
        size (int): Tamanho do ícone (ex: 9 para 16x, 18 para 32x)
        output_path (str): Caminho completo para salvar o arquivo de saída.

    Returns:
        str: Caminho do arquivo salvo se sucesso, None se falha.
    """
    try:
        img = Image.open(image_path)
        crop_box = (x, y, x + size, y + size)
        cropped = img.crop(crop_box)
        
        # Garante que o diretório de saída exista
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cropped.save(output_path)
        # print(f"Ícone salvo como: {output_path}")
        return output_path
    except FileNotFoundError:
        print(f"Arquivo não encontrado para recorte: {image_path}")
        return None
    except Exception as e:
        print(f"Erro ao recortar e salvar imagem {image_path}: {e}")
        return None

def crop_heart_hunger_smart(image_path, icon_type, output_dir, pack_upload_id):
    """
    Recorta automaticamente ícones de coração e fome baseado na resolução da textura
    e salva na pasta de previews.

    Args:
        image_path (str): Caminho para o arquivo icons.png
        icon_type (str): Tipo do ícone ("heart_full", "hunger_full", etc.)
        output_dir (str): Diretório base para salvar as previews (TEMP_PREVIEW_FOLDER/pack_upload_id)
        pack_upload_id (str): ID único do upload do pack para criar subpasta de preview.

    Returns:
        str: Caminho URL estático para a imagem recortada, ou None se falha.
    """
    try:
        resolution = detect_texture_resolution(image_path)
        scale = resolution // 16  # Escala baseada na resolução 16x

        # Coordenadas base para textura 16x (tamanho 9x9)
        # Essas coordenadas são para a sprite sheet padrão do Minecraft.
        # Se um resource pack mudar drasticamente o layout da icons.png, isso pode falhar.
        base_coords = {
            "heart_full": (52, 0),  # Coração cheio
            "hunger_full": (52, 27), # Coxa de frango cheia
            # Você pode adicionar mais aqui se precisar de outras variações:
            # "heart_half": (61, 0),
            # "heart_empty": (16, 0),
            # "hunger_half": (61, 27),
            # "hunger_empty": (16, 27),
        }

        if icon_type not in base_coords:
            print(f"Tipo de ícone inválido para recorte inteligente: {icon_type}")
            return None

        base_x, base_y = base_coords[icon_type]
        scaled_x = base_x * scale
        scaled_y = base_y * scale
        icon_size = 9 * scale # Ícones de vida/fome são 9x9 na base 16x

        # Caminho de saída para a preview recortada
        # Ex: temp_previews/UUID_DO_PACK/heart_full_originalfilename.png
        preview_filename = f"{icon_type}_{os.path.basename(image_path)}" # Ex: heart_full_icons.png
        output_path = os.path.join(output_dir, preview_filename)

        # Recorta e salva a imagem
        saved_path = crop_minecraft_icon(image_path, scaled_x, scaled_y, icon_size, output_path)
        
        if saved_path:
            # Retorna o caminho URL estático que o Flask vai servir
            # O endpoint 'temp_previews' é o que definimos com app.add_url_rule
            return f'/temp_previews/{pack_upload_id}/{preview_filename}'
        return None
    except Exception as e:
        print(f"Erro em crop_heart_hunger_smart para {image_path}, tipo {icon_type}: {e}")
        return None

def generate_animated_gif(image_path, mcmeta_path, output_path, default_frametime=2):
    """
    Gera um GIF animado a partir de uma sprite sheet PNG e um arquivo .mcmeta.

    Args:
        image_path (str): Caminho para o arquivo PNG da sprite sheet.
        mcmeta_path (str): Caminho para o arquivo .mcmeta correspondente.
        output_path (str): Caminho completo para salvar o GIF de saída.
        default_frametime (int): Tempo padrão de cada frame em ticks (1 tick = 50ms).

    Returns:
        str: Caminho do arquivo GIF salvo se sucesso, None se falha.
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        mcmeta_data = {}
        if os.path.exists(mcmeta_path):
            with open(mcmeta_path, 'r') as f:
                mcmeta_data = json.load(f)
        
        animation_props = mcmeta_data.get('animation', {})
        
        # Determina o tamanho de cada frame (assumindo frames verticais)
        # Se não houver 'frametime' ou 'frames' no mcmeta, assumimos uma sprite sheet simples
        # onde a altura da imagem é um múltiplo da largura, e cada frame tem a largura da imagem.
        frame_height = animation_props.get('frametime', default_frametime) * 2 # Placeholder, será ajustado
        
        # Se 'frames' for uma lista, calculamos a altura do frame a partir da altura total
        # e do número de frames. Se não, assumimos que a largura é o tamanho do frame.
        if 'frames' in animation_props and isinstance(animation_props['frames'], list):
            num_frames = len(animation_props['frames'])
            if num_frames > 0:
                frame_height = height // num_frames # Altura de cada frame
            else:
                frame_height = width # Fallback se não tiver frames definidos (ex: 1x1 textura)
        else:
            # Se não há frames definidos explicitamente, assume que a altura total
            # é um múltiplo da largura, e a largura é o tamanho do frame.
            # Ex: 16x48 (3 frames de 16x16)
            if width > 0:
                frame_height = width
                num_frames = height // frame_height
            else: # Caso de imagem inválida
                print(f"Erro: Largura da imagem é zero para {image_path}")
                return None


        frames = []
        for i in range(num_frames):
            # Recorta cada frame
            box = (0, i * frame_height, width, (i + 1) * frame_height)
            frame = img.crop(box)
            frames.append(frame)

        if not frames:
            print(f"Nenhum frame encontrado para gerar GIF de {image_path}")
            return None

        # Calcula a duração de cada frame em milissegundos
        # Minecraft frametime é em ticks (1 tick = 50ms)
        duration_ms = animation_props.get('frametime', default_frametime) * 50

        # Salva o GIF
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Pillow precisa de pelo menos 2 frames para animação. Se for 1, salva como PNG.
        if len(frames) > 1:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=duration_ms,
                loop=0 # 0 significa loop infinito
            )
        else:
            # Se for apenas um frame, salva como PNG
            img.save(output_path.replace('.gif', '.png'))
            output_path = output_path.replace('.gif', '.png')

        print(f"GIF animado salvo como: {output_path}")
        return output_path
    except FileNotFoundError:
        print(f"Arquivo PNG ou MCMETA não encontrado para animação: {image_path} ou {mcmeta_path}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao ler JSON do arquivo .mcmeta: {mcmeta_path}")
        return None
    except Exception as e:
        print(f"Erro ao gerar GIF animado de {image_path}: {e}")
        return None
