from app import create_app
 
app = create_app()
 
if __name__ == "__main__":
    # threaded=True é essencial aqui: o /stream-camera mantém a conexão
    # aberta continuamente (streaming MJPEG), então sem threading o
    # servidor de desenvolvimento consegue atender só UMA requisição por
    # vez e trava (ou falha) qualquer outra rota enquanto o vídeo estiver
    # sendo exibido - incluindo a autenticação facial.
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"], threaded=True)