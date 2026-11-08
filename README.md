# Mundo Perdido

Projeto de aventura 3D em terceira pessoa, desenvolvido em Godot 4.7.2 (última versão estável identificada) para Android.

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
- Mapa Springfield convertido do OBJ original para GLB: 77.296 vértices, 73.243 faces e 9 materiais preservados; o original completo permanece no pacote de auditoria.

Os pacotes originais completos ficam preservados no artefato de auditoria. O APK deve receber somente os recursos necessários à cena, para evitar carregar centenas de modelos sem uso e prejudicar o desempenho em celulares.

## Controles do protótipo

- Joystick esquerdo: movimentação.
- Arrastar o lado direito: girar a câmera.
- Botão Pular.
- Botão Correr.
- Botão Atirar reservado para a próxima etapa de combate.

## Estado

Protótipo inicial de exploração 3D. Build Android 0.1.3 compilado com sucesso em Godot 4.7.2; importação e teste de inicialização headless passaram. Teste visual e de desempenho no aparelho Android ainda pendente.
