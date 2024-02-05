from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp, sp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.utils import get_color_from_hex as colorHEX
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from datetime import datetime, timedelta
from kivymd.uix.list import OneLineListItem
from kivymd.uix.imagelist import MDSmartTile
import json, os, glob, math

class Main(MDScreen):
    def __init__(self, **kwargs):
        super(Main, self).__init__(**kwargs)
        self.menu_items = [{"text": "Create a recipe","height": dp(64), "viewclass": "OneLineListItem", "on_release": self.go_to_create_recipe},
                           {"text": "Edit recipe","height": dp(64), "viewclass": "OneLineListItem", "on_release": self.go_to_edit_recipe}]
        self.menu = MDDropdownMenu(
            items=self.menu_items,
            header_cls=MenuHeader(),
            width_mult=3,)
        
    def display_recipe_files(self, *args):
        recipes_dir = "recipes"
        for file in os.listdir(recipes_dir):
            if file.endswith(".json"):
                with open(os.path.join(recipes_dir, file), 'r') as f:
                    recipe_data = json.load(f)
                recipe_name = recipe_data.get('name', '')  # Pobierz nazwę przepisu
                image_path = recipe_data.get('image_path', '')  # Pobierz ścieżkę do obrazu
                recipe_item = RecipesItem(filename=os.path.join(recipes_dir, file))
                recipe_item.source = image_path
                recipe_item.ids.label.text = recipe_name
                self.ids.container.add_widget(recipe_item)
    
    def display_brew_files(self, *args):
        # Pobierz listę plików .json w katalogu 'mybrew'
        json_files = [f for f in os.listdir('mybrew') if f.endswith('.json')]

        # Posortuj pliki według daty modyfikacji, od najnowszego do najstarszego
        json_files.sort(key=lambda x: os.path.getmtime(os.path.join('mybrew', x)), reverse=True)

        # Iteruj przez posortowane pliki
        for filename in json_files:
            with open(os.path.join('mybrew', filename), 'r') as f:
                data = json.load(f)
            brew_item = MyBrewItem()
            brew_item.ids.brew_name.text = data['Name']
            brew_item.ids.brew_desc.text = data['Description']
            brew_item.ids.brew_date.text = data['Brew date']
            brew_item.ids.bottling_date.text = data['Bottling date']
            self.ids.my_brew_list.add_widget(brew_item)

    def open_menu(self, button):
        self.menu.caller = button
        self.menu.open()

    def go_to_create_recipe(self, *args):
        self.manager.current = 'create_recipe'
        self.menu.dismiss()

    def go_to_edit_recipe(self, *args):
        self.manager.current = 'edit_recipe'
        self.menu.dismiss()

    def on_pre_leave(self, *args):
        self.manager.get_screen('create_recipe').clear_fields()
        self.manager.get_screen('edit_recipe').clear_fields()

    def abv_calc(self):
        try:
            og = float(self.ids.og_field.text.replace(',', '.'))
            fg = float(self.ids.fg_field.text.replace(',', '.'))
            if og < 0 or fg < 0:
                raise ValueError
            abv = (og - fg) / 1.938
            self.ids.abv_result.text = f"Alcohol By Volume: {abv:.2f}%"
        except ValueError:
            self.ids.abv_result.text = "Bad values"

    def clear_ABV_fields(self):
        self.ids.og_field.text = ''
        self.ids.fg_field.text = ''
        self.ids.abv_result.text = ''
    
    def carbonation_calc(self):
        try:
            beer_l = float(self.ids.beer_l_field.text)
            temp_c = float(self.ids.temp_c_field.text)
            desiredVols = float(self.ids.desiredVols_field.text)
        except ValueError:
            self.ids.carbonation_result.text = "All fields must be completed"
            return

        try:
            if self.ids.gluc.active:
                sugar_type = 'gluc'
            elif self.ids.sucrose.active:
                sugar_type = 'sucrose'
            elif self.ids.dme.active:
                sugar_type = 'dme'
            else:
                raise ValueError("You need to choose the type of sugar")
        except ValueError as e:
            self.ids.carbonation_result.text = str(e)
            return

        residualVols = 1.57 * math.pow(0.97, temp_c)
        addedVols = desiredVols - residualVols
        co2_l = addedVols * beer_l
        co2_mol = co2_l / 22.4

        if sugar_type == 'gluc':
            sugar_mol = co2_mol / 2
            sugar_g = sugar_mol * 180
        elif sugar_type == 'sucrose':
            sugar_mol = co2_mol / 4
            sugar_g = sugar_mol * 342
        elif sugar_type == 'dme':
            sugar_mol = co2_mol / 2
            sugar_g = sugar_mol * 180 / 0.60

        self.ids.carbonation_result.text = f"Amount of sugar: {round(sugar_g, 1)}g"

    def clear_carbonation_fields(self):
        self.ids.beer_l_field.text = ''
        self.ids.temp_c_field.text = ''
        self.ids.desiredVols_field.text = ''
        self.ids.carbonation_result.text = ''
        self.ids.gluc.active = False
        self.ids.sucrose.active = False
        self.ids.dme.active = False
    
class CreateRecipe(MDScreen):
    def set_image_path(self, image_path, button_id):
        self.image_path = image_path
        self.ids.light_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'light_beer_btn' else [0,0,0,0]
        self.ids.amber_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'amber_beer_btn' else [0,0,0,0]
        self.ids.black_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'black_beer_btn' else [0,0,0,0]

    def clear_fields(self):
        self.ids.recipe_name.text = ""
        self.ids.recipe_description.text = ""
        self.ids.ingredients.text = ""
        self.ids.steps.text = ""
        self.image_path = ""
        self.ids.error_label.text = ""
        self.ids.light_beer_btn.background_color = [0,0,0,0]
        self.ids.amber_beer_btn.background_color = [0,0,0,0]
        self.ids.black_beer_btn.background_color = [0,0,0,0]

    def save_recipe_as_json(self):
        if not self.ids.recipe_name.text or not self.ids.recipe_description.text or not self.ids.ingredients.text or not self.ids.steps.text or not self.image_path:
            self.ids.error_label.text = "All fields must be completed and an image must be selected"
            return
        recipe = {
            'name': self.ids.recipe_name.text,
            'description': self.ids.recipe_description.text,
            'ingredients': self.ids.ingredients.text.split('\n'),
            'steps': self.ids.steps.text.split('\n\n'),
            'image_path': self.image_path
        }
        if not os.path.exists('recipes'):
            os.makedirs('recipes')
        with open(os.path.join('recipes', f'{recipe["name"]}.json'), 'w') as f:
            json.dump(recipe, f)
        
    def back_to_main(self):
        self.manager.current = 'main'

class EditRecipe(MDScreen):
    def __init__(self, **kwargs):
        super(EditRecipe, self).__init__(**kwargs)
        self.recipe_files = []
        self.selected_recipe = None

    def on_enter(self, *args):
        self.search(None, "")

    def clear_fields(self):
        self.ids.recipe_name.text = ""
        self.ids.recipe_description.text = ""
        self.ids.ingredients.text = ""
        self.ids.steps.text = ""
        self.image_path = ""
        self.ids.error_label.text = ""
        self.ids.light_beer_btn.background_color = [0,0,0,0]
        self.ids.amber_beer_btn.background_color = [0,0,0,0]
        self.ids.black_beer_btn.background_color = [0,0,0,0]

    def set_image_path(self, image_path, button_id):
        self.image_path = image_path
        self.ids.light_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'light_beer_btn' else [0,0,0,0]
        self.ids.amber_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'amber_beer_btn' else [0,0,0,0]
        self.ids.black_beer_btn.background_color = colorHEX("#FF9800") if button_id == 'black_beer_btn' else [0,0,0,0]

    def search(self, instance, value):
        self.ids.search_results.clear_widgets()
        search_term = value.lower()
        for file in glob.glob("recipes/*.json"):
            filename = os.path.basename(file)
            name, ext = os.path.splitext(filename)
            if search_term in name.lower():
                list_item = OneLineListItem(text=name)
                list_item.bind(on_release=self.load_recipe)
                self.ids.search_results.add_widget(list_item)

    def load_recipe(self, instance):
        self.selected_recipe = instance.text
        with open(os.path.join('recipes', f'{instance.text}.json'), 'r') as f:
            recipe = json.load(f)
        self.ids.recipe_name.text = recipe['name']
        self.ids.recipe_description.text = recipe['description']
        self.ids.ingredients.text = '\n'.join(recipe['ingredients'])
        self.ids.steps.text = '\n\n'.join(recipe['steps'])
        self.image_path = recipe['image_path']
        button_id = os.path.splitext(os.path.basename(self.image_path))[0] + "_btn"
        self.set_image_path(self.image_path, button_id)

    def overwrite_recipe(self):
        if not self.ids.recipe_name.text or not self.ids.recipe_description.text or not self.ids.ingredients.text or not self.ids.steps.text or not self.image_path:
            self.ids.error_label.text = "All fields must be completed and an image must be selected"
            return
        recipe = {
            'name': self.ids.recipe_name.text,
            'description': self.ids.recipe_description.text,
            'ingredients': self.ids.ingredients.text.split('\n'),
            'steps': self.ids.steps.text.split('\n\n'),
            'image_path': self.image_path
        }
        if not os.path.exists('recipes'):
            os.makedirs('recipes')
        with open(os.path.join('recipes', f'{self.selected_recipe}.json'), 'w') as f:
            json.dump(recipe, f)

    def save_as_new_recipe(self):
        if not self.ids.recipe_name.text or not self.ids.recipe_description.text or not self.ids.ingredients.text or not self.ids.steps.text or not self.image_path:
            self.ids.error_label.text = "All fields must be completed and an image must be selected"
            return
        recipe = {
            'name': self.ids.recipe_name.text,
            'description': self.ids.recipe_description.text,
            'ingredients': self.ids.ingredients.text.split('\n'),
            'steps': self.ids.steps.text.split('\n'),
            'image_path': self.image_path
        }
        if not os.path.exists('recipes'):
            os.makedirs('recipes')
        filename = f'{recipe["name"]}.json'
        if os.path.exists(os.path.join('recipes', filename)):
            filename = f'{recipe["name"]}_edited.json'
        with open(os.path.join('recipes', filename), 'w') as f:
            json.dump(recipe, f)

    def back_to_main(self):
        self.manager.current = 'main'

class Recipe(MDScreen):
    recipe_data = ObjectProperty(None)  # Nowy atrybut do przechowywania danych przepisu

    def back_to_main(self):
        self.manager.current = 'main'

    def display_recipe(self, recipe):
        self.recipe_data = recipe  # Przechowaj dane przepisu
        self.ids.recipe_name.text = recipe['name']
        self.ids.image_path.source = recipe['image_path']
        self.ids.recipe_description.text = recipe['description']
        self.ids.recipe_ingredients.text = '\n'.join(recipe['ingredients'])

    def get_recipe_data(self):
        return self.recipe_data  # Metoda do pobierania danych przepisu

    def go_to_brew(self):
        app = MDApp.get_running_app()
        app.root.current = 'brew'
        app.root.get_screen('brew').display_brew(self.get_recipe_data())

class Brew(MDScreen):
    step_number = NumericProperty(0)
    brew_date = ObjectProperty(None)
    bottling_date = ObjectProperty(None)

    def on_pre_enter(self):
        Clock.schedule_once(self.set_dates, 0)

    def set_dates(self, dt):
        self.ids.brew_date.text = datetime.now().strftime('%Y-%m-%d')
        self.ids.bottling_date.text = (datetime.now() + timedelta(weeks=2)).strftime('%Y-%m-%d')

    def back_to_main(self):
        self.manager.current = 'main'
        self.clear_brew()

    def display_brew(self, recipe):
        self.recipe = recipe
        self.ids.brew_name.title = recipe['name']
        self.display_step()

    def display_step(self):
        self.ids.step_nr.text = f'Step {self.step_number + 1}'
        self.ids.step_text.text = self.recipe['steps'][self.step_number]
        self.ids.pre_step.opacity = 0 if self.step_number == 0 else 1
        self.ids.next_step.icon = "check" if self.step_number == len(self.recipe['steps']) - 1 else "arrow-right"
        if self.step_number == len(self.recipe['steps']) - 1:
            self.ids.brew_date_container.opacity = 1
            self.ids.bottling_date_container.opacity = 1
        else:
            self.ids.brew_date_container.opacity = 0
            self.ids.bottling_date_container.opacity = 0

    def finish_brew(self):
        data = {
            'Name': self.recipe['name'],
            'Description': self.recipe['description'],
            'Image': self.recipe['image_path'],
            'Brew date': self.ids.brew_date.text,
            'Bottling date': self.ids.bottling_date.text
        }
        if not os.path.exists('mybrew'):
            os.makedirs('mybrew')
        brew_files = [f for f in os.listdir('mybrew') if f.startswith('brew_')]
        if brew_files:
            max_brew_nr = max(int(f.split('_')[1].split('.')[0]) for f in brew_files)
        else:
            max_brew_nr = 0
        with open(os.path.join('mybrew', f'brew_{max_brew_nr + 1}.json'), 'w') as f:
            json.dump(data, f)

        self.go_to_my_brew()
    
    def go_to_my_brew(self):
        self.manager.current = 'main'
        self.manager.get_screen('main').ids.bottom_navigation.switch_tab('scr3')
        MDApp.get_running_app().update_main_screen()

    def next_step(self):
        if self.step_number < len(self.recipe['steps']) - 1:
            self.step_number += 1
            self.display_step()
        else:
            self.finish_brew()

    def pre_step(self):
        if self.step_number > 0:
            self.step_number -= 1
            self.display_step()

    def clear_brew(self):
        self.ids.step_nr.text = ''
        self.ids.step_text.text = ''
        self.step_number = 0
        self.ids.pre_step.opacity = 1
        self.ids.next_step.icon = "arrow-right"
        self.ids.brew_date.text = ''
        self.ids.bottling_date.text = ''

class MenuHeader(MDBoxLayout):
    pass

class RecipesItem(MDSmartTile):
    filename = StringProperty()
    recipe_name = StringProperty()

    def on_tile_release(self):
        # Wczytaj dane z pliku JSON
        with open(self.filename, 'r') as f:
            recipe = json.load(f)

        # Przejdź do ekranu "recipe" i wyświetl dane przepisu
        app = MDApp.get_running_app()
        app.root.current = 'recipe'
        app.root.get_screen('recipe').display_recipe(recipe)

class MyBrewItem(MDBoxLayout):
    brew_name = StringProperty()
    brew_desc = StringProperty()
    brew_date = StringProperty()
    bottling_date = StringProperty()

class MyApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Dark"

        sm = MDScreenManager()
        
        sm.add_widget(Main(name="main"))
        sm.add_widget(Recipe(name="recipe"))
        sm.add_widget(Brew(name="brew"))
        sm.add_widget(CreateRecipe(name="create_recipe"))
        sm.add_widget(EditRecipe(name="edit_recipe"))

        return Builder.load_file("main.kv")
    
    def on_start(self):
        Clock.schedule_once(self.root.get_screen('main').display_recipe_files)
        Clock.schedule_once(self.root.get_screen('main').display_brew_files)
    
    def update_main_screen(self):
        main_screen = self.root.get_screen('main')
        main_screen.ids.container.clear_widgets()
        main_screen.ids.my_brew_list.clear_widgets()
        main_screen.display_recipe_files()
        main_screen.display_brew_files()

if __name__=="__main__":
    MyApp().run()