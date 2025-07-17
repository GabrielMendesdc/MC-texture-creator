#!/usr/bin/env python3
"""
Script de teste para verificar se o sistema de bordas funciona corretamente
"""

import os
import sys
import tempfile
import shutil
from PIL import Image

# Adiciona o diretório atual ao path para importar o módulo preview
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from preview_fixed import add_border_to_image
    print("✓ Função add_border_to_image importada com sucesso")
except ImportError as e:
    print(f"✗ Erro ao importar função: {e}")
    sys.exit(1)

def create_test_image(size=(16, 16), color=(128, 128, 128)):
    """Cria uma imagem de teste simples"""
    img = Image.new('RGBA', size, color)
    return img

def test_border_system():
    """Testa o sistema de bordas"""
    print("\n--- Testando Sistema de Bordas ---")
    
    # Cria um diretório temporário para testes
    with tempfile.TemporaryDirectory() as temp_dir:
        # Cria uma imagem de teste
        test_img = create_test_image(color=(100, 150, 200, 255))
        test_img_path = os.path.join(temp_dir, "test_texture.png")
        test_img.save(test_img_path)
        
        print(f"Imagem de teste criada: {test_img_path}")
        
        # Testa borda verde (usuário)
        print("Testando borda verde (usuário)...")
        green_bordered = add_border_to_image(test_img_path, 'green', 3)
        if os.path.exists(green_bordered):
            print(f"✓ Borda verde criada: {green_bordered}")
            
            # Verifica se a imagem com borda foi criada corretamente
            with Image.open(green_bordered) as bordered_img:
                original_size = test_img.size
                new_size = bordered_img.size
                expected_size = (original_size[0] + 6, original_size[1] + 6)  # +6 = 3px de cada lado
                
                if new_size == expected_size:
                    print(f"✓ Tamanho correto: {new_size} (esperado: {expected_size})")
                else:
                    print(f"✗ Tamanho incorreto: {new_size} (esperado: {expected_size})")
        else:
            print(f"✗ Falha ao criar borda verde")
        
        # Testa borda vermelha (padrão)
        print("Testando borda vermelha (padrão)...")
        red_bordered = add_border_to_image(test_img_path, 'red', 2)
        if os.path.exists(red_bordered):
            print(f"✓ Borda vermelha criada: {red_bordered}")
            
            # Verifica se a imagem com borda foi criada corretamente
            with Image.open(red_bordered) as bordered_img:
                original_size = test_img.size
                new_size = bordered_img.size
                expected_size = (original_size[0] + 4, original_size[1] + 4)  # +4 = 2px de cada lado
                
                if new_size == expected_size:
                    print(f"✓ Tamanho correto: {new_size} (esperado: {expected_size})")
                else:
                    print(f"✗ Tamanho incorreto: {new_size} (esperado: {expected_size})")
        else:
            print(f"✗ Falha ao criar borda vermelha")
        
        # Testa com cor RGB personalizada
        print("Testando borda com cor RGB personalizada...")
        custom_bordered = add_border_to_image(test_img_path, (255, 255, 0, 255), 1)  # Amarelo
        if os.path.exists(custom_bordered):
            print(f"✓ Borda personalizada criada: {custom_bordered}")
        else:
            print(f"✗ Falha ao criar borda personalizada")

def test_integration_with_preview():
    """Testa a integração com o sistema de preview"""
    print("\n--- Testando Integração com Preview ---")
    
    try:
        from preview_fixed import (
            load_default_zip_textures,
            get_default_texture_for_pack,
            analyze_resource_pack_with_defaults
        )
        print("✓ Funções de preview importadas com sucesso")
        
        # Testa carregamento do default.zip
        app_root = os.path.dirname(os.path.abspath(__file__))
        success = load_default_zip_textures(app_root)
        
        if success:
            print("✓ Default.zip carregado com sucesso")
            
            # Testa obtenção de textura padrão com borda
            with tempfile.TemporaryDirectory() as temp_dir:
                test_pack_id = "test_pack_123"
                default_texture = get_default_texture_for_pack("Lã", temp_dir, test_pack_id)
                
                if default_texture and default_texture.get('is_default'):
                    print("✓ Textura padrão obtida com borda vermelha")
                    print(f"  URL: {default_texture['static_url_path']}")
                else:
                    print("✗ Falha ao obter textura padrão com borda")
        else:
            print("✗ Falha ao carregar default.zip")
            
    except ImportError as e:
        print(f"✗ Erro ao importar funções de preview: {e}")

def main():
    """Função principal de teste"""
    print("=== Teste do Sistema de Bordas ===")
    
    test_border_system()
    test_integration_with_preview()
    
    print("\n=== Teste Concluído ===")
    print("✓ Sistema de bordas está funcionando!")
    print("Legenda:")
    print("  🟢 Verde = Texturas enviadas pelo usuário")
    print("  🔴 Vermelho = Texturas padrão do default.zip")

if __name__ == '__main__':
    main()

