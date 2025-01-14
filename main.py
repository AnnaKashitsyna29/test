import time

import arcade
import arcade.gui

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Пингви"
RESIZABLE = True
SELECTED_SKIN = "pngegg"

CHARACTER_SCALING = 0.5
TILE_SCALING = 0.5
COIN_SCALING = 0.5

PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

TEXTURE_LEFT = 1
TEXTURE_RIGHT = 0

SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING

PLAYER_START_X = 64
PLAYER_START_Y = 225

LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_FOREGROUND = "Foreground"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_DONT_TOUCH = "Don't Touch"


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.current_texture = 0
        self.scale = CHARACTER_SCALING
        self.texture_direction = TEXTURE_RIGHT

        self.textures_idle_pair = arcade.texture.load_texture_pair(f"sprites/player/{SELECTED_SKIN}.png")
        self.textures_jump_pair = arcade.texture.load_texture_pair(
            f"sprites/player/animation/jump/jump_{SELECTED_SKIN}.png")

        self.textures_fall_pair = arcade.texture.load_texture_pair(
            f"sprites/player/animation/fall/fall_{SELECTED_SKIN}.png")
        self.walk_textures = []
        for i in range(2):
            texture = arcade.texture.load_texture_pair(f"sprites/player/animation/walk/step{i + 1}_{SELECTED_SKIN}.png")
            self.walk_textures.append(texture)

        self.texture = self.textures_idle_pair[self.texture_direction]
        self.end_of_map = 0

        self.level = 1
        self.reset_score = True

        self.update_texture_limit = 0

    def update(self):

        if self.change_x < 0 and self.texture_direction == TEXTURE_RIGHT:
            self.texture_direction = TEXTURE_LEFT
            self.texture = self.textures_idle_pair[self.texture_direction]
        elif self.change_x > 0 and self.texture_direction == TEXTURE_LEFT:
            self.texture_direction = TEXTURE_RIGHT
            self.texture = self.textures_idle_pair[self.texture_direction]

        if self.change_y < 0:
            self.texture = self.textures_fall_pair[self.texture_direction]
            return

        if self.change_y > 0:
            self.texture = self.textures_jump_pair[self.texture_direction]
            return

        if self.change_x == 0:
            self.texture = self.textures_idle_pair[self.texture_direction]
            return

        self.update_texture_limit += abs(self.change_x)

        if self.update_texture_limit >= 30:
            self.current_texture += 1
            if self.current_texture > 1:
                self.current_texture = 0
            self.update_texture_limit = 0

        self.texture = self.walk_textures[self.current_texture][self.texture_direction]


class MyGame(arcade.View):
    def __init__(self):
        super().__init__()

        self.scene: arcade.Scene = None

        self.camera = None

        self.gui_camera = None

        self.tile_map = None

        self.score = 0

        self.reset_score = True

        self.end_of_map = 0

        self.level = 1

        self.player_sprite: arcade.Sprite = None

        self.physics_engine: arcade.PhysicsEnginePlatformer = None

        arcade.set_background_color(arcade.color.CORNFLOWER_BLUE)

    def setup(self):
        self.camera = arcade.Camera(self.window.width, self.window.height)
        self.gui_camera = arcade.Camera(self.window.width, self.window.height)

        map_name = f":resources:tiled_maps/map2_level_{self.level}.json"

        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_COINS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            },
        }

        self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        if self.reset_score:
            self.score = 0
        self.reset_score = True
        self.scene.add_sprite_list_after("Player", LAYER_NAME_FOREGROUND)

        # region Player sprite
        self.player_sprite = Player()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.scene.add_sprite("Player", self.player_sprite)
        # endregion

        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        if self.tile_map.background_color:
            arcade.set_background_color(self.tile_map.background_color)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, gravity_constant=GRAVITY, walls=self.scene["Platforms"]
        )
        self.physics_engine.enable_multi_jump(2)

    def on_show_view(self):
        self.setup()

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()

        self.gui_camera.use()

        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.WHITE,
            18,
        )

    def on_key_press(self, key, modifiers):

        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.physics_engine.increment_jump_counter()
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
                self.camera.viewport_height / 2
        )

        # Don't let camera travel past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def on_update(self, delta_time):
        self.physics_engine.update()
        self.player_sprite.update()

        for coin in self.scene[LAYER_NAME_COINS]:
            if ((coin.center_x - coin.width / 2 <= self.player_sprite.center_x <= coin.center_x + coin.width / 2) and
                    (
                            coin.center_y - coin.height / 2 <= self.player_sprite.center_y <= coin.center_y + coin.height / 2)):
                self.scene[LAYER_NAME_COINS].remove(coin)
                self.score += 1

        for elem in self.scene[LAYER_NAME_DONT_TOUCH]:
            if ((elem.center_x - elem.width / 2 <= self.player_sprite.center_x <= elem.center_x + elem.width / 2) and
                    (
                            elem.center_y - elem.height / 2 <= self.player_sprite.center_y <= elem.center_y + elem.height / 2)):
                game_over = GameMenuView("Lose", color=arcade.color.RED)
                self.window.show_view(game_over)

        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

        if self.player_sprite.center_x >= self.end_of_map:
            self.level += 1

            self.reset_score = False
            if self.level == 3:
                game_over = GameMenuView("Win", color=arcade.color.GREEN)
                self.window.show_view(game_over)
                return

            self.setup()
        self.center_camera_to_player()


class GameSettings(arcade.View):
    def __init__(self):
        super().__init__()
        self.skins_box = None
        self.v_box = None
        self.manager = None

    def on_show_view(self):
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        self.v_box = arcade.gui.UIBoxLayout()
        self.skins_box = arcade.gui.UIBoxLayout(vertical=False)

        label = arcade.gui.UILabel(text="Settings", font_size=30, text_color=arcade.color.WHITE)
        self.v_box.add(label.with_space_around(bottom=20))

        skin1 = arcade.gui.UITextureButton(texture=arcade.texture.load_texture(f"sprites/player/pngegg.png"), width=150,
                                           height=150, )
        self.skins_box.add(skin1.with_space_around(left=10))

        skin2 = arcade.gui.UITextureButton(texture=arcade.texture.load_texture(f"sprites/player/pngegg_green.png"),
                                           width=150, height=150, )
        self.skins_box.add(skin2.with_space_around(left=10))

        skin3 = arcade.gui.UITextureButton(texture=arcade.texture.load_texture(f"sprites/player/pngegg_pink.png"),
                                           width=150, height=150, )
        self.skins_box.add(skin3.with_space_around(left=10))

        @skin1.event("on_click")
        def on_click_quit(event):
            global SELECTED_SKIN
            SELECTED_SKIN = "pngegg"
            label.text = "Selected skin: Default"

        @skin2.event("on_click")
        def on_click_quit(event):
            global SELECTED_SKIN
            SELECTED_SKIN = "pngegg_green"
            label.text = "Selected skin: Green"

        @skin3.event("on_click")
        def on_click_quit(event):
            global SELECTED_SKIN
            SELECTED_SKIN = "pngegg_pink"
            label.text = "Selected skin: Pink"

        self.v_box.add(self.skins_box)

        label_text = ""

        if SELECTED_SKIN == "pngegg":
            label_text = "Defualt"
        elif SELECTED_SKIN == "pngegg_green":
            label_text = "Green"
        else:
            label_text = "Pink"

        label = arcade.gui.UILabel(text=f"Selected skin: {label_text}", font_size=15, text_color=arcade.color.WHITE)
        self.v_box.add(label.with_space_around(bottom=20))

        quit_button = arcade.gui.UIFlatButton(text="Quit", width=200)
        self.v_box.add(quit_button.with_space_around(top=20))

        @quit_button.event("on_click")
        def on_click_quit(event):
            menu_view = GameMenuView("Menu", arcade.color.WHITE)
            self.window.show_view(menu_view)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def on_draw(self):
        self.clear()
        self.manager.draw()


class GameMenuView(arcade.View):

    def __init__(self, label, color=arcade.color.WHITE):
        super().__init__()
        self.v_box = None
        self.manager = None
        self.label_text = label
        self.color = color

    def on_show_view(self):
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        self.v_box = arcade.gui.UIBoxLayout()

        label = arcade.gui.UILabel(text=self.label_text, font_size=30, text_color=self.color)
        self.v_box.add(label.with_space_around(bottom=20))

        # Create the buttons
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=200)
        self.v_box.add(start_button.with_space_around(bottom=20))

        settings_button = arcade.gui.UIFlatButton(text="Settings", width=200)
        self.v_box.add(settings_button.with_space_around(bottom=20))

        # Again, method 1. Use a child class to handle events.
        quit_button = arcade.gui.UIFlatButton(text="Quit", width=200)
        self.v_box.add(quit_button)

        @quit_button.event("on_click")
        def on_click_quit(event):
            arcade.close_window()

        @settings_button.event("on_click")
        def on_click_settings(event):
            settings_view = GameSettings()
            self.window.show_view(settings_view)

        @start_button.event("on_click")
        def on_click_start(event):
            game_view = MyGame()
            self.window.show_view(game_view)

        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def on_draw(self):
        self.clear()
        self.manager.draw()


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game_view = GameMenuView(label="Menu")
    window.show_view(game_view)
    arcade.run()


if __name__ == '__main__':
    main()
