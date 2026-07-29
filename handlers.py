import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from utils import topics, save_topics

# Conversation states
TITLE, DESCRIPTION, CATEGORY, DEADLINE = range(4)

# Temporary storage for conversation data
user_data_temp = {}

def start_command(update: Update, context: CallbackContext):
    """Send a welcome message when /start is issued."""
    welcome_text = """
📝 **Welcome to Create Topic Bot!**

This bot helps you create and manage topics easily.

**Available Commands:**
- /new - Create a new topic
- /my - View all your topics
- /delete - Delete a topic
- /help - Show help message

Click /new to get started!
    """
    update.message.reply_text(welcome_text, parse_mode='Markdown')

def help_command(update: Update, context: CallbackContext):
    """Send a help message."""
    help_text = """
🤔 **How to use this bot:**

1️⃣ Click /new to start creating a topic
2️⃣ Enter a title for your topic
3️⃣ Add a description (or type 'skip' to skip)
4️⃣ Choose a category (Work, Personal, Study, Other)
5️⃣ Set a deadline (or type 'skip' to skip)
6️⃣ Your topic is saved!

**Other Commands:**
- /my - View all your topics
- /delete - Delete a topic
- /cancel - Cancel current operation
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def new_topic_start(update: Update, context: CallbackContext):
    """Start the new topic creation process."""
    user_id = str(update.effective_user.id)
    user_data_temp[user_id] = {}
    
    update.message.reply_text(
        "📝 **Let's create a new topic!**\n\n"
        "First, what's the **title** of your topic?\n"
        "(Type /cancel to cancel)",
        parse_mode='Markdown'
    )
    return TITLE

def topic_title(update: Update, context: CallbackContext):
    """Store the topic title."""
    user_id = str(update.effective_user.id)
    title = update.message.text.strip()
    
    if len(title) > 100:
        update.message.reply_text(
            "❌ Title is too long! Please keep it under 100 characters.\n"
            "Try again or type /cancel to cancel."
        )
        return TITLE
    
    user_data_temp[user_id]['title'] = title
    
    update.message.reply_text(
        f"✅ Great! Title: *{title}*\n\n"
        "Now, add a **description** for your topic.\n"
        "(Type 'skip' to skip this step)",
        parse_mode='Markdown'
    )
    return DESCRIPTION

def topic_description(update: Update, context: CallbackContext):
    """Store the topic description."""
    user_id = str(update.effective_user.id)
    description = update.message.text.strip()
    
    if description.lower() == 'skip':
        description = ''
    
    user_data_temp[user_id]['description'] = description
    
    # Category selection
    keyboard = [
        [
            InlineKeyboardButton("💼 Work", callback_data="cat_work"),
            InlineKeyboardButton("🏠 Personal", callback_data="cat_personal"),
        ],
        [
            InlineKeyboardButton("📚 Study", callback_data="cat_study"),
            InlineKeyboardButton("🎯 Other", callback_data="cat_other"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "📂 **Select a category** for your topic:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CATEGORY

def topic_category(update: Update, context: CallbackContext):
    """Store the topic category."""
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    category = query.data.replace('cat_', '')
    
    # Map category to display name
    category_map = {
        'work': '💼 Work',
        'personal': '🏠 Personal',
        'study': '📚 Study',
        'other': '🎯 Other'
    }
    
    user_data_temp[user_id]['category'] = category
    
    query.edit_message_text(
        f"✅ Category selected: *{category_map.get(category, category)}*\n\n"
        "📅 Now, set a **deadline** for your topic.\n"
        "(Format: YYYY-MM-DD or type 'skip' to skip)",
        parse_mode='Markdown'
    )
    return DEADLINE

def topic_deadline(update: Update, context: CallbackContext):
    """Store the topic deadline and save the topic."""
    user_id = str(update.effective_user.id)
    deadline_input = update.message.text.strip()
    
    # Validate deadline format if not skipped
    deadline = None
    if deadline_input.lower() != 'skip':
        try:
            deadline = datetime.strptime(deadline_input, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            update.message.reply_text(
                "❌ Invalid date format! Please use YYYY-MM-DD format.\n"
                "Example: 2024-12-31\n"
                "Try again or type 'skip' to skip."
            )
            return DEADLINE
    
    # Save the topic
    topic_data = user_data_temp[user_id]
    topic_data['deadline'] = deadline
    topic_data['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Store in topics dictionary
    if user_id not in topics:
        topics[user_id] = []
    
    topics[user_id].append(topic_data)
    save_topics()
    
    # Clear temporary data
    del user_data_temp[user_id]
    
    # Confirmation message
    category_map = {
        'work': '💼 Work',
        'personal': '🏠 Personal',
        'study': '📚 Study',
        'other': '🎯 Other'
    }
    
    response = f"""
✅ **Topic Created Successfully!**

📌 **Title:** {topic_data['title']}
📂 **Category:** {category_map.get(topic_data['category'], topic_data['category'])}
"""
    
    if topic_data['description']:
        response += f"📝 **Description:** {topic_data['description']}\n"
    
    if topic_data['deadline']:
        response += f"📅 **Deadline:** {topic_data['deadline']}\n"
    
    response += f"\n🆔 **Topic ID:** {len(topics[user_id])}"
    response += "\n\nUse /my to view all your topics."
    
    update.message.reply_text(response, parse_mode='Markdown')
    return ConversationHandler.END

def my_topics(update: Update, context: CallbackContext):
    """Show all topics for the user."""
    user_id = str(update.effective_user.id)
    
    if user_id not in topics or not topics[user_id]:
        update.message.reply_text(
            "📭 You haven't created any topics yet!\n"
            "Use /new to create your first topic."
        )
        return
    
    response = "📋 **Your Topics:**\n\n"
    category_map = {
        'work': '💼 Work',
        'personal': '🏠 Personal',
        'study': '📚 Study',
        'other': '🎯 Other'
    }
    
    for idx, topic in enumerate(topics[user_id], 1):
        response += f"**{idx}. {topic['title']}**\n"
        response += f"   📂 {category_map.get(topic['category'], topic['category'])}\n"
        if topic.get('description'):
            desc = topic['description']
            response += f"   📝 {desc[:50]}...\n" if len(desc) > 50 else f"   📝 {desc}\n"
        if topic.get('deadline'):
            response += f"   📅 {topic['deadline']}\n"
        response += "\n"
    
    response += "Use /delete to remove a topic."
    update.message.reply_text(response, parse_mode='Markdown')

def delete_topic(update: Update, context: CallbackContext):
    """Delete a topic."""
    user_id = str(update.effective_user.id)
    
    if user_id not in topics or not topics[user_id]:
        update.message.reply_text(
            "📭 You don't have any topics to delete.\n"
            "Use /new to create your first topic."
        )
        return
    
    # Show topics with numbers for deletion
    keyboard = []
    for idx, topic in enumerate(topics[user_id], 1):
        label = f"{idx}. {topic['title'][:30]}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"del_{idx-1}")])
    
    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "🗑️ **Select a topic to delete:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def button_callback(update: Update, context: CallbackContext):
    """Handle button callbacks."""
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Handle delete confirmation
    if data.startswith('del_'):
        if data == 'del_cancel':
            query.edit_message_text("✅ Deletion cancelled.")
            return
        
        try:
            idx = int(data.replace('del_', ''))
            deleted_topic = topics[user_id].pop(idx)
            save_topics()
            
            query.edit_message_text(
                f"✅ Topic deleted: *{deleted_topic['title']}*",
                parse_mode='Markdown'
            )
        except (IndexError, ValueError):
            query.edit_message_text("❌ Error deleting topic. Please try again.")
    
    # Handle conversation category selection
    elif data.startswith('cat_'):
        # This is handled in topic_category function
        pass

def cancel_conversation(update: Update, context: CallbackContext):
    """Cancel the current conversation."""
    user_id = str(update.effective_user.id)
    if user_id in user_data_temp:
        del user_data_temp[user_id]
    
    update.message.reply_text(
        "❌ Topic creation cancelled.\n"
        "Click /new to start again."
    )
    return ConversationHandler.END
