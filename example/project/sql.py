
SQL_QUERIES = [

{
    'slug': 'artists',
    'title': 'Some Artists',
    'sql': """
select *
from backend_artist
where name like '%%' || $name || '%%'
""",
    'notes': "",
},

]
