import psycopg2
from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired
from psycopg2 import sql  # 确保导入 sql 模块
from flask import flash, redirect, url_for
import configparser

from flask import Flask, render_template, request, jsonify
from zhipuai import ZhipuAI

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')  # 读取配置文件

# 获取数据库配置
DB_CONFIG = {
    'dbname': config['database']['dbname'],
    'user': config['database']['user'],
    'password': config['database']['password'],
    'host': config['database']['host'],
    'port': int(config['database']['port'])  # 将端口号转为整数
}

# 连接数据库
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

# 初始化 Flask 应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 用于表单安全验证

# Flask 表单定义
class ModelForm(FlaskForm):
    name = StringField('模型名称', validators=[DataRequired()])
    model_type = StringField('模型类型', validators=[DataRequired()])
    model_location = StringField('模型部署位置', validators=[DataRequired()])
    model_owner = StringField('模型所属', validators=[DataRequired()])
    model_download = StringField('模型下载地址', validators=[DataRequired()])
    model_description = TextAreaField('模型描述', validators=[DataRequired()])
    model_remark = TextAreaField('模型备注')

class PluginForm(FlaskForm):
    name = StringField('插件名称', validators=[DataRequired()])
    plugin_location = StringField('插件部署位置', validators=[DataRequired()])
    plugin_download = StringField('插件下载地址', validators=[DataRequired()])
    plugin_owner = StringField('插件所属', validators=[DataRequired()])
    plugin_remark = TextAreaField('插件备注')
    install_date = DateField('安装时间', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('提交')

# 首页，展示模型和插件表单
@app.route('/', methods=['GET', 'POST'])
def index():
    model_form = ModelForm()
    plugin_form = PluginForm()
    
    if model_form.validate_on_submit():
        # 保存模型信息到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        # 调整插入语句以匹配 "模型信息" 表字段
        cursor.execute('''
            INSERT INTO public."模型信息"(
                "模型名称", "模型类型", "模型部署位置", "模型所属", 
                "模型下载地址", "模型描述", "模型备注"
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            model_form.name.data,
            model_form.model_type.data,
            model_form.model_location.data,
            model_form.model_owner.data,
            model_form.model_download.data,
            model_form.model_description.data,
            model_form.model_remark.data
        ))
        conn.commit()
        cursor.close()
        conn.close()
        flash('模型添加成功！', 'success')

        return redirect(url_for('index'))  # 重定向到首页

# 处理插件表单提交
    if plugin_form.validate_on_submit():
        # 获取表单数据
        name = plugin_form.name.data
        plugin_location = plugin_form.plugin_location.data
        plugin_download = plugin_form.plugin_download.data
        plugin_owner = plugin_form.plugin_owner.data
        plugin_remark = plugin_form.plugin_remark.data
        install_date = plugin_form.install_date.data

        # 保存插件信息到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(""" 
            INSERT INTO public."插件信息"(
                "插件名称", "插件部署位置", "插件下载地址", "插件所属", 
                "插件备注", "安装时间"
            ) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, plugin_location, plugin_download, plugin_owner, plugin_remark, install_date))

        conn.commit()
        cursor.close()
        conn.close()
        flash('插件添加成功！', 'success')
        return redirect(url_for('index'))  # 重定向到首页

    return render_template('index.html', model_form=model_form, plugin_form=plugin_form)
    
# 显示所有模型
@app.route('/models')
def models():
     # 获取当前页数，如果没有则默认第1页
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20个模型

    # 计算分页的偏移量
    offset = (page - 1) * per_page

    # 连接数据库并执行分页查询
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 使用 psycopg2.sql 构建安全查询
    query = sql.SQL('SELECT * FROM public."模型信息" ORDER BY id ASC LIMIT {limit} OFFSET {offset}').format(
        limit=sql.Placeholder(), offset=sql.Placeholder()
    )
    
    cursor.execute(query, [per_page, offset])
    models = cursor.fetchall()

    # 获取总模型数
    cursor.execute('SELECT COUNT(*) FROM public."模型信息"')
    total_models = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # 计算总页数
    total_pages = (total_models // per_page) + (1 if total_models % per_page > 0 else 0)

    return render_template('models.html', models=models, page=page, total_pages=total_pages)

# 显示所有插件
@app.route('/plugins')
def plugins():
     # 获取当前页数，如果没有则默认第1页
    page = request.args.get('page', 1, type=int)
    per_page = 20  # 每页显示20个插件

    # 计算分页的偏移量
    offset = (page - 1) * per_page

    # 连接数据库并执行分页查询
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 使用 psycopg2.sql 构建安全查询
    query = sql.SQL('SELECT * FROM public."插件信息" ORDER BY id ASC LIMIT {limit} OFFSET {offset}').format(
        limit=sql.Placeholder(), offset=sql.Placeholder()
    )
    
    cursor.execute(query, [per_page, offset])
    plugins = cursor.fetchall()

    # 获取总插件数
    cursor.execute('SELECT COUNT(*) FROM public."插件信息"')
    total_plugins = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # 计算总页数
    total_pages = (total_plugins // per_page) + (1 if total_plugins % per_page > 0 else 0)
    return render_template('plugins.html', plugins=plugins, page=page, total_pages=total_pages)

# 搜索模型
@app.route('/search1', methods=['GET', 'POST'])
def search1():
    query = ''
    models = []  # 默认没有结果

    if request.method == 'POST':
        query = request.form['query']  # 获取表单提交的查询关键词

        if query:
            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 模糊查询模型名称
            cursor.execute("""
                SELECT * FROM public."模型信息"
                WHERE "模型名称" ILIKE %s
                ORDER BY "模型名称" ASC
            """, ('%' + query + '%',))
            
            models = cursor.fetchall()  # 获取查询结果
            cursor.close()
            conn.close()

    # 返回结果到模板
    return render_template('search1.html', models=models, query=query)


@app.route('/search2', methods=['GET', 'POST'])
def search2():
    query = ''
    plugins = []  # 默认没有结果

    if request.method == 'POST':
        query = request.form['query']  # 获取表单提交的查询关键词

        if query:
            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 模糊查询模型名称
            cursor.execute("""
                SELECT * FROM public."插件信息"
                WHERE "插件名称" ILIKE %s
                ORDER BY "插件名称" ASC
            """, ('%' + query + '%',))
            
            plugins = cursor.fetchall()  # 获取查询结果
            cursor.close()
            conn.close()

    # 返回结果到模板
    return render_template('search2.html', plugins=plugins, query=query)


# 读取 API 密钥
def read_api_key(file_path="GLM4-Flash.key"):
    with open(file_path, "r") as file:
        api_key = file.read().strip()  # 读取并去掉多余的空白字符
    return api_key

# 使用读取到的 API 密钥初始化客户端
api_key = read_api_key("GLM4-Flash.key")  # 根据实际路径调整文件名
client = ZhipuAI(api_key=api_key)

# 用来存储对话历史
messages = []

# 调用模型获取响应
def get_model_response(action, query):
    try:
        # 确保query字符串以UTF-8格式处理
        query = query.encode('utf-8').decode('utf-8')  # 强制转换为UTF-8

        # 控制台调试输出
        print(f"调用模型: {action}，输入内容: {query}")

        # 根据不同的操作，构造提示词
        if action == 'translate':
            prompt = f"翻译以下中文为英文：{query}"
        elif action == 'expand':
            prompt = f"将以下内容扩写并翻译：{query}"

        # 打印构造的提示词，确认无误
        print(f"构造的提示词: {prompt}")

        # 构造消息
        messages = [{"role": "user", "content": prompt}]

        # 调用 ZhipuAI 接口（确保已正确初始化 client）
        response = client.chat.completions.create(
            model="glm-4-flash",  # 使用的模型
            messages=messages  # 传递对话历史
        )

        # 获取模型响应
        model_response = response.choices[0].message.content

        # 打印模型的响应，确认返回内容
        print(f"模型的响应: {model_response}")

        # 返回模型响应的内容
        return model_response

    except Exception as e:
        print(f"API 调用发生错误: {e}")  # 错误时的调试信息
        return f"发生错误，请稍后再试。错误详情: {str(e)}"


# Flask 路由
@app.route('/translate', methods=['GET', 'POST'])
def translate():
    translated_text = ""
    expanded_text = ""
    query = ''  # 默认为空

    if request.method == 'POST':
        query = request.form['query']  # 获取输入框中的中文文本
        query = query.encode('utf-8', 'ignore').decode('utf-8')  # 清理编码问题
        action = request.form.get('action')  # 获取用户选择的操作（翻译或扩写）

        if query:
            if action == 'translate':
                # 调用 ZhipuAI 接口进行翻译
                translated_text = get_model_response('translate', query)
            elif action == 'expand':
                # 调用 ZhipuAI 接口进行扩写
                expanded_text = get_model_response('expand', query)

    return render_template('translate.html', translated_text=translated_text, 
                           expanded_text=expanded_text, query=query)



# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True)
