from fpdf import FPDF, HTMLMixin
 
class HTML2PDF(FPDF, HTMLMixin):
    pass
 
def generate_users(users):
    html = '''<h1 align="center">Lista de Usuários</h1>
                <table width="100%">
                    <tr width="100%">
                        <th width="25%">Usuário</th>
                        <th width="25%">Email</th>
                        <th width="25%">Arquivo de Imagem</th>
                        <th width="25%">Tipo de Usuário</th>
                    </tr> '''

    for user in users:
        html += f'''<tr width="100%">
                    <td align="center" width="25%">{user.username}</td>
                    <td align="center" width="25%">{user.email}</td>
                    <td align="center" width="25%">{user.image_file}</td>
                    <td align="center" width="25%">{user.user_type}</td>
                    </tr>'''
    
    html += '''</table>'''

    path = 'mysite/static/pdf_files/lista_usuarios.pdf'

    pdf = HTML2PDF()
    pdf.add_page()
    pdf.write_html(html)
    pdf.output(path)

    return path

def generate_posts(posts):
    html = '''<h1 align="center">Lista de Posts</h1>
                <table width="100%">
                    <tr width="100%">
                        <th width="25%">Usuário</th>
                        <th width="25%">Título</th>
                        <th width="25%">Votos</th>
                        <th width="25%">Data</th>
                    </tr> '''

    for post in posts:
        html += f'''<tr width="100%">
                    <td align="center" width="25%">{post.author.username}</td>
                    <td align="center" width="25%">{post.title}</td>
                    <td align="center" width="25%">{post.total_score}</td>
                    <td align="center" width="25%">{post.date_posted}</td>
                    </tr>'''
    
    html += '''</table>'''

    path = 'mysite/static/pdf_files/lista_posts.pdf'

    pdf = HTML2PDF()
    pdf.add_page()
    pdf.write_html(html)
    pdf.output(path, 'F')

    return path
