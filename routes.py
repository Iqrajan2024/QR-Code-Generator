import os
from flask import Flask, render_template, request, redirect,url_for,send_file, send_from_directory
import qrcode
from io import BytesIO
from base64 import b64encode
from qrcode.image.pil import PilImage
from PIL import Image
from urllib.parse import quote
from flask_mail import Mail,Message 
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
import qrcode.constants
from flask_bcrypt import Bcrypt

from models import User


def register_routes(app,db,bcrypt):
   
    @app.route('/')
    def home():
        
        return render_template('index.html')

    @app.route('/generate', methods=['POST','GET'])
    def generateQR():
        try:
            data = request.form.to_dict()
            if not data:
                return"Error:No data provided",400
        
            link = data.get('link')
            box_size = int(data.get('box_size',10))
            border_size = int(data.get('border_size',4))
            foreground_hex = data.get('foreground_color','#000000')
            background_hex = data.get('background_color','#ffffff')
            foreground_rgb = tuple(int(foreground_hex[i:i+2],16) for i in (1,3,5))
            background_rgb = tuple(int(background_hex[i:i+2],16) for i in (1,3,5)) 
            error_correction_level = data.get('error_correction', 'M').upper()
            error_correction_dict = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M, 
                'Q': qrcode.constants.ERROR_CORRECT_Q, 
                'H': qrcode.constants.ERROR_CORRECT_H

            }
            error_correction = error_correction_dict.get(error_correction_level, qrcode.constants.ERROR_CORRECT_M)

            
            if not link or not isinstance(link,str):
                return "Error: Invalid URL provided",400


            qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction,
            box_size=box_size,
            border=border_size
            )
            
            qr.add_data(link)
            qr.make(fit=True)

            

            qr_image = qr.make_image(
                back_color= background_rgb,
                fill_color= foreground_rgb,
                image_factory=qrcode.image.pil.PilImage            
            )

            logo_file = request.files.get('logo')
            if logo_file:
                logo = Image.open(logo_file).convert("RGBA")
                basewidth = box_size * 5
                wpercent = (basewidth / float(logo.size[0]))
                hsize = int((float(logo.size[1]) * float(wpercent)))
                logo = logo.resize((basewidth,hsize), Image.LANCZOS)
                qr_image = qr_image.convert("RGBA")
                pos = ((qr_image.size[0] - logo.size[0]) // 2, (qr_image.size[1] - logo.size[1]) // 2)
                qr_image.paste(logo, pos,mask=logo)

                
            
            qr_image_io = BytesIO()
            qr_image.save(qr_image_io, 'PNG')
            qr_image_io.seek(0)

            base64_img = "data:image/png;base64," +  b64encode(qr_image_io.getvalue()).decode('ascii')
            

            if not os.path.exists(app.config['QR_CODE_DIR']): 
                os.makedirs(app.config['QR_CODE_DIR'])
            filename = f"qr_{data.get('link')}.png" 
            file_path = os.path.join(app.config['QR_CODE_DIR'], filename)
            qr_image.save(file_path)
            share_url = url_for('serve_image', filename=filename, _external=True)
            encoded_share_url = quote(share_url, safe=":/")
            

            return render_template('index.html', data=base64_img, data_url=url_for('static', filename=f'qrcodes/{filename}'),qr_code_url = encoded_share_url)
        
        except Exception as e:
            return render_template('index.html',error=str(e))
        
    @app.route('/qrcodes/<filename>')
    def serve_image(filename):
        return send_from_directory(app.config['QR_CODE_DIR'],filename)

    @app.route('/generate')
    def download_qr():
        try:
            # Retrieve the last-generated QR code (implement caching or session logic if needed)
            qr_image_io = BytesIO()
            qr_image_io.seek(0)
            return send_file(
                qr_image_io,
                as_attachment=True,
                download_name="qrcode.png",
                mimetype="image/png"
            )
        except Exception as e:
            return render_template('index.html', error=str(e))

    @app.route('/signup', methods = ['GET', 'POST'])
    def signup():

        if request.method == 'GET':
            return render_template('signup.html')
        elif request.method == ' POST':
            form = signup-form
            username = request.form.get('username')
            password = request.form.get('password')

            if form.validate_on_submit():
              hashed_password = bcrypt.generate_password_hash(form.password.data)
              new_user = User(username = form.username.data, password = hashed_password)
              db.session.add(new_user)
              db.session.commit()
              return redirect(url_for('index'))



     
    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            form = login-form()
            username = request.form.get('username')
            password = request.form.get('password')

            if form.validate_on_submit():
            
                user = User.query.filter(User.username==form.username.data).first()
    
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    return redirect(url_for('index'))
    

    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))



    