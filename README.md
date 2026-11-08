# Mundo Perdido

Projeto de aventura 3D em terceira pessoa, desenvolvido em Godot 4 para Android.

## Estrutura atual

- `game/`: projeto Godot 4, cena principal, scripts de movimento/câmera e HUD touch.
- `tools/audit_assets.py`: inventário e extração segura dos ZIPs originais.
- `tools/inspect_nested_zips.py`: inspeção de ZIPs encontrados dentro dos pacotes.
- `tools/extract_rar_assets.py`: extração do arquivo RAR que contém a geometria do mapa Springfield.
- `tools/prepare_game_assets.py`: seleciona e organiza os recursos originais para importação na Godot.
- `reports/asset-audit/`: inventários publicados dos arquivos e formatos.
- GitHub Actions gera o pacote integral de assets e executa a compilação Android.

## Recursos já identificados

- Personagem KayKit Mannequin Medium em GLB.
- Animações KayKit Rig Medium em GLB.
- Kit de ruínas com modelos GLB.
- Kit de natureza com modelos glTF e texturas.
- Mapa Springfield com atlas de texturas e geometria OBJ armazenada em arquivo RAR interno.

Os pacotes originais completos ficam preservados no artefato de auditoria. O APK deve receber somente os recursos necessários à cena, para evitar carregar centenas de modelos sem uso e prejudicar o desempenho em celulares.

## Controles do protótipo

- Joystick esquerdo: movimentação.
- Arrastar o lado direito: girar a câmera.
- Botão Pular.
- Botão Correr.
- Botão Atirar reservado para a próxima etapa de combate.

## Estado

Protótipo inicial de exploração e importação dos assets. A compilação e os testes de importação Android ainda precisam terminar com sucesso antes de considerar o APK pronto para teste.
