from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import csv, json

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent / 'bar-site'
reference = json.loads((ROOT/'reference-foods.json').read_text())
ids = reference['usda_food_ids']
facts = reference['ingredient_values_per_100g']
facts.update(whey={'kcal':373,'protein':74,'fat':4.2,'carbs':9.7},plant={'kcal':399,'protein':73,'fat':7.6,'carbs':6.7},isolate={'kcal':375,'protein':78.125,'fat':3.125,'carbs':6.25},gainer={'kcal':376,'protein':15,'fat':1.9,'carbs':75})
def nearest(v, unit=1): return int((Decimal(str(v))/unit).quantize(Decimal('1'),rounding=ROUND_HALF_UP)*unit)
def nutrition(recipe):
    raw = {key:sum(facts[food][key]*grams/100 for food,grams in recipe) for key in ['kcal','protein','fat','carbs']}
    out = {key:nearest(value,5 if key=='kcal' else 1) for key,value in raw.items()}
    if raw['kcal'] and out['kcal']==0: out['kcal']=5
    return {'approximate':True,'per':'расчётная порция','values':out,'unrounded':{k:round(v,3) for k,v in raw.items()}}
facts['caramel']={'kcal':323/1.293,'protein':0,'fat':0,'carbs':79.3/1.293}
items=[]
def add(id,category,name,price,composition='',image=None,recipe=None,assumption='',volume_ml=None,pending=None,badge=None):
    item=dict(id=id,category=category,name=name,price_rub=price,composition=composition,image=image,volume_ml=volume_ml,badge=badge)
    item['nutrition']=nutrition(recipe) if recipe else {'approximate':True,'values':None,'reason':pending}
    item['nutrition']['assumption']=assumption
    item['nutrition']['calculation_recipe_g']=recipe
    items.append(item)

add('breakfast','smoothies','На завтрак',350,'Банан, овсянка, протеин.','breakfast', [('banana',100),('oats',30),('whey',30)], 'Банан 100 г, сухая овсянка 30 г, сывороточный протеин 30 г. Вода не меняет КБЖУ. Молоко, сахар и сиропы в расчёт не включены.',badge='С ПРОТЕИНОМ')
add('berry','smoothies','Ягодный',300,'Банан, ягоды.','berry',[('banana',100),('strawberry',100/3),('blueberry',100/3),('raspberry',100/3)],'Банан 100 г и ягоды 100 г. Для оценки взята смесь клубники, черники и малины в равных долях. Вода — по консистенции; без молока, сахара и сиропов.')
add('fruit','smoothies','Фруктовый',250,'Банан, киви, яблоко.','fruit',[('banana',100),('kiwi',60),('apple',80)],'Банан 100 г, киви 60 г, яблоко 80 г. Вода — по консистенции; без молока, сахара и сиропов.')
add('green','smoothies','Зелёный смузи',250,'Шпинат, банан, яблоко.','green',[('spinach',30),('banana',100),('apple',80)],'Шпинат 30 г, банан 100 г, яблоко 80 г. Вода — по консистенции; без молока, сахара и сиропов.',badge='ЗЕЛЁНЫЙ ВКУС')
add('bumble','drinks','Бамбл-кофе',300,'Апельсиновый фреш, кофе, карамельный сироп.','bumble',[('orange',210),('espresso',30),('caramel',19.395)],'Апельсиновый фреш 200 мл (примерно 210 г), эспрессо 30 мл и карамельный сироп 15 мл (примерно 19,4 г). Сироп учтён по справочной этикетке MONIN. Это расчётные количества; фактическую дозировку и марку сиропа клуба нужно уточнить.',badge='С КАРАМЕЛЬЮ')
for id,name,price,kind in [('whey','Протеин сывороточный',280,'whey'),('plant','Протеин растительный',290,'plant'),('isolate','Протеин изолят',330,'isolate')]:
    add(id,'protein',name,price,image='protein',recipe=[(kind,30)],assumption='Расчёт для 30 г порошка на воде. Марка и вкус не указаны: использована справочная этикетка аналогичного продукта, а не подтверждённая рецептура клуба. При приготовлении на молоке КБЖУ будут выше.')
for id,name,price in [('bcaa','BCAA',110),('creatine','Креатин',130),('preworkout','Предтрен',130)]:
    add(id,'sport',name,price,pending='Нужны марка, форма продукта и масса порции. КБЖУ уточняются по этикетке; отсутствие цифр не означает нулевую калорийность.')
add('gainer','sport','Гейнер',220,recipe=[('gainer',50)],assumption='Расчёт для условной порции 50 г сухого гейнера на воде по этикетке продукта-аналога. Фактическую марку и размер порции клуба нужно уточнить.')
for id,name,price,parts in [('apple','Яблочный',250,[('apple_juice',1)]),('apple-carrot','Яблочно-морковный',250,[('apple_juice',.5),('carrot',.5)]),('orange','Апельсиновый',300,[('orange',1)]),('apple-orange','Яблочно-апельсиновый',300,[('apple_juice',.5),('orange',.5)]),('grapefruit','Грейпфрутовый',320,[('grapefruit',1)]),('orange-grapefruit','Апельсиново-грейпфрутовый',320,[('orange',.5),('grapefruit',.5)])]:
    add('fresh-'+id,'fresh',name,price,recipe=[(k,260*share) for k,share in parts],assumption='250 мл сока приняты примерно за 260 г. Для смешанных фрешей использовано соотношение 1:1. Без добавленного сахара; значения зависят от сырья. Для яблочного и морковного соков использованы справочные аналоги без добавленного сахара.',volume_ml=250)
add('tea','drinks','Чай классический',30,recipe=[('tea',200)],assumption='Условная чашка чёрного чая 200 мл, без сахара, мёда и молока. Объём чашки в исходном меню не указан.')
add('fruit-tea','drinks','Фруктовый чай',120,pending='Не указана рецептура: настой, свежие фрукты, пюре, мёд и сироп дают разную пищевую ценность. Нужен состав и масса ингредиентов.')
add('coffee','drinks','Кофе',80,recipe=[('espresso',30)],assumption='Для оценки взята порция эспрессо 30 мл без сахара и молока. Вид кофе и объём в исходном меню не указаны; это расчётный ориентир.')
images = {
    'whey':'protein', 'plant':'plant', 'isolate':'isolate',
    'bcaa':'bcaa', 'creatine':'creatine.jpg', 'preworkout':'preworkout', 'gainer':'gainer',
    'fresh-apple':'fresh-apple', 'fresh-apple-carrot':'fresh-apple-carrot',
    'fresh-orange':'fresh-orange', 'fresh-apple-orange':'fresh-apple-orange',
    'fresh-grapefruit':'fresh-grapefruit', 'fresh-orange-grapefruit':'fresh',
    'tea':'tea', 'fruit-tea':'fruit-tea', 'coffee':'coffee'
}
descriptions = {
    'whey':'Классический белковый коктейль.',
    'plant':'Белковый коктейль на растительной основе.',
    'isolate':'Коктейль на основе протеина-изолята.',
    'bcaa':'Порция аминокислот BCAA.',
    'creatine':'Порция креатина.',
    'preworkout':'Предтренировочный комплекс.',
    'gainer':'Коктейль на основе гейнера.',
    'fresh-apple':'Свежий яблочный сок.',
    'fresh-apple-carrot':'Яблоко и морковь.',
    'fresh-orange':'Свежий апельсиновый сок.',
    'fresh-apple-orange':'Яблоко и апельсин.',
    'fresh-grapefruit':'Свежий грейпфрутовый сок.',
    'fresh-orange-grapefruit':'Апельсин и грейпфрут.',
    'tea':'Горячий чай для приятной паузы.',
    'fruit-tea':'Яркий фруктовый вкус.',
    'coffee':'Ароматный кофе.'
}
for item in items:
    if item['id'] in images: item['image'] = images[item['id']]
    item['description'] = descriptions.get(item['id'], item['composition'])
assert len(items)==21
assert len({item['image'] for item in items}) == 21
sources=[
 {'id':'caramel','name':'GEORGES MONIN — спецификация карамельного сиропа-аналога','url':'https://www.cfw.co.uk/Media/PDF%20Spec%20Sheets/Monin/Spec-Sheet-Monin-Syrup-Caramel.pdf','note':'323 ккал и 79,3 г углеводов на 100 мл, плотность 1,293 г/мл. Для бамбл-кофе принято 15 мл сиропа. Марка клуба не подтверждена.'},
 {'id':'usda','name':'USDA Standard Reference 28','url':'https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/methods-and-application-of-food-composition-laboratory/mafcl-site-pages/sr11-sr28/','note':'Продукты и соки, значения на 100 г. Яблочный и морковный соки — справочные аналоги.'},
 {'id':'whey','name':'Optimum Nutrition Gold Standard Whey — этикетка аналога','url':'https://www.optimumnutrition.com/de-de/products/gold-standard-100-whey-protein-powder-eu?variant=52105833120011','note':'373 ккал, Б 74, Ж 4,2, У 9,7 г на 100 г. Это не подтверждение марки, используемой клубом.'},
 {'id':'plant','name':'Optimum Nutrition Plant — этикетка аналога','url':'https://www.optimumnutrition.com/de-de/products/gold-standard-100-plant-based-protein-powder-eu?variant=52105842557195','note':'399 ккал, Б 73, Ж 7,6, У 6,7 г на 100 г. Это не подтверждение марки, используемой клубом.'},
 {'id':'isolate','name':'Dymatize ISO100 — этикетка аналога','url':'https://dymatize.com/products/iso100-gourmet-chocolate?pr_rd_page=1','note':'120 ккал, Б 25, Ж 1, У 2 г на 32 г; пересчитано на 30 г. Это не подтверждение марки клуба.'},
 {'id':'gainer','name':'Optimum Nutrition Serious Mass — этикетка аналога','url':'https://www.optimumnutrition.com/en-gb/products/serious-mass-weight-gainer-protein-powder-eu?variant=52105828925707','note':'376 ккал, Б 15, Ж 1,9, У 75 г на 100 г. Для оценки принята порция 50 г; это не подтверждение марки клуба.'}
]
categories=[{'id':'smoothies','name':'Смузи'},{'id':'protein','name':'Протеин'},{'id':'sport','name':'Спортивное питание'},{'id':'fresh','name':'Фреши'},{'id':'drinks','name':'Напитки'}]
data={'brand':'Линия спорта','menu_source':{'type':'owner_photo','file':'IMG_20261029_234450_636.jpg','date':'2026-10-29'},'owner_updates':[{'date':'2026-10-30','change':'Бамбл-кофе с карамельным сиропом, 300 ₽; состав уточнён владельцем.'},{'date':'2026-10-30','change':'L-карнитин заменён на креатин в разделе «Спортивное питание». Цена 130 ₽ перенесена без изменения из прежней карточки; требует подтверждения.'}],'common_menu_for_all_clubs':True,'nutrition_method':{'status':'approximate_not_verified_recipe','rounding':'Калории до 5 ккал, БЖУ до целого грамма. Значения рассчитаны на обозначенную расчётную порцию, не на 100 г.','notice':'Граммовки для расчёта предварительные. Реальные КБЖУ зависят от рецептуры, марки порошка, вкуса и основы напитка.','usda_food_ids':ids,'ingredient_values_per_100g':facts,'sources':sources},'categories':categories,'items':items}
(SITE/'menu.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(ROOT/'menu-summary.txt').write_text('\n'.join(f"{x['name']}: {x['price_rub']} ₽ | {x['nutrition']['values'] or 'КБЖУ уточняется'} | {x['nutrition']['assumption']}" for x in items))
print(f"21 menu items; {sum(x['nutrition']['values'] is not None for x in items)} estimated portions, {sum(x['nutrition']['values'] is None for x in items)} awaiting product/recipe details.")
