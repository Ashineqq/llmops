from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class AppCompletionReq(FlaskForm):
    query = StringField(
        "query",
        validators=[
            DataRequired(message="请输入查询内容"),
            Length(max=1024, message="查询内容最多1024个字符"),
        ],
    )
