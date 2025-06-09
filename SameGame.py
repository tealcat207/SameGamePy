import pygame
import random
import sys

# --- Pygame Initialization ---
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
# BLOCK_SIZE is now dynamically calculated, but we keep a base for fonts and initial layout
BASE_BLOCK_SIZE = 40
MIN_BLOCK_SIZE = 25 # Minimum size for a block to ensure visibility

# Base colors
ALL_POSSIBLE_COLORS = [
    (209, 4, 11),    # Red
    (6, 201, 58),    # Green
    (4, 103, 209),    # Blue
    (230, 242, 2),  # Yellow
    (14, 240, 240)   # Cyan
]

BACKGROUND_COLOR = (30, 30, 30) # Dark grey
TEXT_COLOR = (255, 255, 255) # White
HIGHLIGHT_COLOR = (200, 200, 200) # Light grey for selection
BUTTON_COLOR = (50, 50, 50)
HOVER_COLOR = (80, 80, 80)

# --- Setup Screen ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("SameGame")
font = pygame.font.Font(None, 36) # Default font, size 36
large_font = pygame.font.Font(None, 48) # Default font, size 48
medium_font = pygame.font.Font(None, 30) # Medium font for settings

# --- Game Variables (now with adjustable defaults) ---
board = []
score = 0
selected_blocks = []
game_over = False

# Adjustable game settings - Default to a horizontal board
current_num_colors = 5
current_board_width = 20 # Changed from 15 to make it horizontal by default
current_board_height = 10 # Changed from 12 to make it horizontal by default

# Dynamic constants (initialized here, but updated in create_board)
DYNAMIC_BLOCK_SIZE = BASE_BLOCK_SIZE
SIDE_MARGIN = 0
TOP_MARGIN = 0
COLORS = ALL_POSSIBLE_COLORS[:current_num_colors]


# --- Game Functions ---

def create_board():
    """
    Initializes the game board with random colored blocks based on current settings.
    Dynamically calculates block size and margins.
    """
    global board, score, game_over, SIDE_MARGIN, TOP_MARGIN, DYNAMIC_BLOCK_SIZE, COLORS

    # Calculate available space for the board
    # Account for score text and buttons at the top, and some padding at the bottom
    available_height = SCREEN_HEIGHT - 150 # Adjust this value if more top/bottom UI is added
    available_width = SCREEN_WIDTH - 50 # Some padding on sides

    # Calculate potential block size based on width and height
    block_size_from_width = available_width // current_board_width if current_board_width > 0 else MIN_BLOCK_SIZE
    block_size_from_height = available_height // current_board_height if current_board_height > 0 else MIN_BLOCK_SIZE

    # Choose the smaller of the two to ensure it fits, and enforce a minimum size
    DYNAMIC_BLOCK_SIZE = max(MIN_BLOCK_SIZE, min(block_size_from_width, block_size_from_height))

    # Recalculate margins based on the new DYNAMIC_BLOCK_SIZE
    # Center the board horizontally
    SIDE_MARGIN = (SCREEN_WIDTH - current_board_width * DYNAMIC_BLOCK_SIZE) // 2
    # Place board below score/buttons, centered vertically within remaining space
    TOP_MARGIN = (SCREEN_HEIGHT - (current_board_height * DYNAMIC_BLOCK_SIZE)) // 2 # Center vertically
    # Ensure TOP_MARGIN gives enough space at the top for score/quit button
    TOP_MARGIN = max(TOP_MARGIN, 60) # At least 60px from top

    # Select the subset of colors based on current_num_colors
    COLORS = ALL_POSSIBLE_COLORS[:current_num_colors]
    if not COLORS: # Fallback if somehow 0 colors selected (shouldn't happen with min_colors check)
        COLORS = [(255,255,255)] # Default to white if no colors are picked

    board = [[random.randint(0, current_num_colors - 1) for _ in range(current_board_width)] for _ in range(current_board_height)]
    score = 0
    selected_blocks = [] # Clear selection on new game
    game_over = False

def draw_board():
    """Draws all blocks on the screen using DYNAMIC_BLOCK_SIZE."""
    for row in range(current_board_height):
        for col in range(current_board_width):
            block_color_index = board[row][col]
            if block_color_index != -1: # -1 indicates an empty/removed block
                x = SIDE_MARGIN + col * DYNAMIC_BLOCK_SIZE
                y = TOP_MARGIN + row * DYNAMIC_BLOCK_SIZE
                color = COLORS[block_color_index]
                pygame.draw.rect(screen, color, (x, y, DYNAMIC_BLOCK_SIZE, DYNAMIC_BLOCK_SIZE), 0)
                # Draw a border for blocks
                pygame.draw.rect(screen, (50, 50, 50), (x, y, DYNAMIC_BLOCK_SIZE, DYNAMIC_BLOCK_SIZE), 1)

def find_connected_blocks(start_row, start_col, color_index):
    """
    Performs a Breadth-First Search (BFS) to find all connected blocks
    of the same color starting from (start_row, start_col).
    Returns a list of (row, col) tuples for all connected blocks.
    """
    if not (0 <= start_row < current_board_height and 0 <= start_col < current_board_width):
        return [] # Invalid starting position

    if board[start_row][start_col] == -1 or board[start_row][start_col] != color_index:
        return []

    queue = [(start_row, start_col)]
    visited = set([(start_row, start_col)])
    connected = []

    while queue:
        r, c = queue.pop(0)
        connected.append((r, c))

        # Check neighbors (up, down, left, right)
        neighbors = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        for nr, nc in neighbors:
            # Check bounds and if neighbor is same color and not visited
            if 0 <= nr < current_board_height and 0 <= nc < current_board_width and \
               board[nr][nc] == color_index and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return connected

def apply_gravity():
    """Makes blocks fall down to fill empty spaces."""
    for col in range(current_board_width):
        empty_slots = 0
        for row in range(current_board_height - 1, -1, -1): # Iterate from bottom up
            if board[row][col] == -1:
                empty_slots += 1
            elif empty_slots > 0:
                # Move block down by the number of empty slots
                board[row + empty_slots][col] = board[row][col]
                board[row][col] = -1 # Clear original position

def shift_columns():
    """Shifts columns to the left if an entire column is empty."""
    empty_cols_count = 0
    new_board = [[-1 for _ in range(current_board_width)] for _ in range(current_board_height)]
    current_new_col = 0

    for col in range(current_board_width):
        is_column_empty = True
        for row in range(current_board_height):
            if board[row][col] != -1:
                is_column_empty = False
                break
        
        if not is_column_empty:
            # Copy non-empty column to the new board
            for row in range(current_board_height):
                new_board[row][current_new_col] = board[row][col]
            current_new_col += 1
            
    # Overwrite the old board with the shifted new board
    for row in range(current_board_height):
        for col in range(current_board_width):
            board[row][col] = new_board[row][col]


def calculate_score(num_removed_blocks):
    """Calculates score based on the number of blocks removed."""
    # Common SameGame scoring: (n-2)^2, where n is number of blocks removed
    if num_removed_blocks >= 2:
        return (num_removed_blocks - 2) ** 2
    return 0

def check_game_over():
    """Checks if there are any possible moves left."""
    for r in range(current_board_height):
        for c in range(current_board_width):
            if board[r][c] != -1:
                # Check if there are at least two connected blocks
                connected = find_connected_blocks(r, c, board[r][c])
                if len(connected) >= 2:
                    return False # Possible move found
    return True # No more moves


def draw_button(rect, text, mouse_pos, clicked):
    """Draws a button and returns True if clicked."""
    is_hover = rect.collidepoint(mouse_pos)
    color = HOVER_COLOR if is_hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, 0, 5) # Draw with rounded corners
    pygame.draw.rect(screen, TEXT_COLOR, rect, 2, 5) # Border

    text_surface = medium_font.render(text, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)
    return clicked and is_hover

def settings_menu():
    """Displays and handles the settings menu."""
    global current_num_colors, current_board_width, current_board_height

    menu_running = True
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    clicked = True

        screen.fill(BACKGROUND_COLOR)

        # Title
        title_text = large_font.render("Game Settings", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_text, title_rect)

        y_offset = 150 # Starting Y position for options

        # Number of Colors Setting
        num_colors_text = medium_font.render(f"Number of Colors: {current_num_colors}", True, TEXT_COLOR)
        screen.blit(num_colors_text, (SCREEN_WIDTH // 2 - 150, y_offset))

        # Buttons for changing number of colors
        btn_minus_colors = pygame.Rect(SCREEN_WIDTH // 2 + 100, y_offset, 40, 30)
        btn_plus_colors = pygame.Rect(SCREEN_WIDTH // 2 + 150, y_offset, 40, 30)

        if draw_button(btn_minus_colors, "-", mouse_pos, clicked):
            if current_num_colors > 4:
                current_num_colors -= 1
        if draw_button(btn_plus_colors, "+", mouse_pos, clicked):
            if current_num_colors < len(ALL_POSSIBLE_COLORS):
                current_num_colors += 1

        y_offset += 70

        # Board Width Setting
        board_width_text = medium_font.render(f"Board Width: {current_board_width}", True, TEXT_COLOR)
        screen.blit(board_width_text, (SCREEN_WIDTH // 2 - 150, y_offset))

        # Buttons for changing board width
        btn_minus_width = pygame.Rect(SCREEN_WIDTH // 2 + 100, y_offset, 40, 30)
        btn_plus_width = pygame.Rect(SCREEN_WIDTH // 2 + 150, y_offset, 40, 30)

        if draw_button(btn_minus_width, "-", mouse_pos, clicked):
            if current_board_width > 5:
                current_board_width -= 1
        if draw_button(btn_plus_width, "+", mouse_pos, clicked):
            if current_board_width < 25: # Max reasonable width
                current_board_width += 1

        y_offset += 70

        # Board Height Setting
        board_height_text = medium_font.render(f"Board Height: {current_board_height}", True, TEXT_COLOR)
        screen.blit(board_height_text, (SCREEN_WIDTH // 2 - 150, y_offset))

        # Buttons for changing board height
        btn_minus_height = pygame.Rect(SCREEN_WIDTH // 2 + 100, y_offset, 40, 30)
        btn_plus_height = pygame.Rect(SCREEN_WIDTH // 2 + 150, y_offset, 40, 30)

        if draw_button(btn_minus_height, "-", mouse_pos, clicked):
            if current_board_height > 5:
                current_board_height -= 1
        if draw_button(btn_plus_height, "+", mouse_pos, clicked):
            if current_board_height < 20: # Max reasonable height
                current_board_height += 1

        y_offset += 100

        # Back Button
        back_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 75, y_offset, 150, 50)
        if draw_button(back_button_rect, "Back to Game", mouse_pos, clicked):
            menu_running = False # Exit settings menu

        pygame.display.flip()


# --- Main Game Loop ---
def game_loop():
    global score, selected_blocks, game_over

    game_state = "menu" # Initial state: "menu", "playing", "settings"

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    clicked = True
            elif event.type == pygame.KEYDOWN:
                if game_state == "playing" and game_over and event.key == pygame.K_r:
                    # Restart game
                    create_board()
                    selected_blocks = []
                    game_state = "playing" # Ensure state is playing after restart

        screen.fill(BACKGROUND_COLOR) # Clear screen

        if game_state == "menu":
            # Display Start Game button
            start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, 200, 60)
            if draw_button(start_button_rect, "Start Game", mouse_pos, clicked):
                create_board()
                game_state = "playing"

            # Display Settings button
            settings_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30, 200, 60)
            if draw_button(settings_button_rect, "Settings", mouse_pos, clicked):
                game_state = "settings"

            # Title for menu
            title_text = large_font.render("SameGame", True, TEXT_COLOR)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
            screen.blit(title_text, title_rect)

        elif game_state == "settings":
            settings_menu()
            game_state = "menu" # After exiting settings, go back to main menu

        elif game_state == "playing":
            if not game_over and clicked:
                mouse_x, mouse_y = mouse_pos
                # Convert mouse coordinates to board coordinates
                col = (mouse_x - SIDE_MARGIN) // DYNAMIC_BLOCK_SIZE # Use DYNAMIC_BLOCK_SIZE
                row = (mouse_y - TOP_MARGIN) // DYNAMIC_BLOCK_SIZE # Use DYNAMIC_BLOCK_SIZE

                # Check if click is within board boundaries
                if 0 <= row < current_board_height and 0 <= col < current_board_width:
                    clicked_color_index = board[row][col]

                    if clicked_color_index != -1: # If a block is clicked
                        # Find connected blocks
                        current_selection = find_connected_blocks(row, col, clicked_color_index)

                        if len(current_selection) >= 2: # Only select if 2 or more blocks
                            if selected_blocks == current_selection:
                                # If the same group is clicked again, remove them
                                for r, c in selected_blocks:
                                    board[r][c] = -1 # Mark as empty
                                score += calculate_score(len(current_selection))
                                selected_blocks = [] # Clear selection

                                # Apply gravity and shift columns after removal
                                apply_gravity()
                                shift_columns()
                                game_over = check_game_over() # Check if game is over
                            else:
                                # New group selected, highlight them
                                selected_blocks = current_selection
                        else:
                            # Clicked on a single block or isolated block, deselect
                            selected_blocks = []

            # --- Drawing for game board ---
            draw_board() # Draw all blocks

            # Draw selected blocks with a highlight
            for r, c in selected_blocks:
                x = SIDE_MARGIN + c * DYNAMIC_BLOCK_SIZE
                y = TOP_MARGIN + r * DYNAMIC_BLOCK_SIZE
                # Draw a slightly lighter rectangle over the selected block
                pygame.draw.rect(screen, HIGHLIGHT_COLOR, (x, y, DYNAMIC_BLOCK_SIZE, DYNAMIC_BLOCK_SIZE), 2) # 2 pixel border

            # Display score
            score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
            screen.blit(score_text, (SIDE_MARGIN, 10))

            # Display game over message
            if game_over:
                game_over_text = large_font.render("Game Over!", True, (255, 50, 50))
                text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(game_over_text, text_rect)

                restart_text = font.render("Press R to Restart", True, TEXT_COLOR)
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
                screen.blit(restart_text, restart_rect)

            # Add a 'Quit' button for the game screen
            quit_button_rect = pygame.Rect(SCREEN_WIDTH - 150, 10, 140, 40)
            if draw_button(quit_button_rect, "Quit Game", mouse_pos, clicked):
                game_state = "menu" # Go back to menu when quitting game

        pygame.display.flip() # Update the full display Surface to the screen

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    game_loop()
