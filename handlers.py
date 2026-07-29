import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils import topics, save_topics

# Conversation states
TITLE, DESCRIPTION, CATEGORY, DEADLINE = range(4)

# Temporary storage for conversation data
user_data_temp = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def new_topic_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the new topic creation process."""
    user_id = str(update.effective_user.id)
    user_data_temp[user_id] = {}
    
    await update.message.reply_text(
        "📝 **Let's create a new topic!**\n\n"
        "First, what's the **title** of your topic?\n"
        "(Type /cancel to cancel)",
        parse_mode='Markdown'
    )
    return TITLE

async def topic_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the topic title."""
    user_id = str(update.effective_user.id)
    title = update.message.text.strip()
    
    if len(title) > 100:
        await update.message.reply_text(
            "❌ Title is too long! Please keep it under 100 characters.\n"
            "Try again or type /cancel to cancel."
        )
        return TITLE
    
    user_data_temp[user_id]['title'] = title
    
    await update.message.reply_text(
        f"✅ Great! Title: *{title}*\n\n"
        "Now, add a **description** for your topic.\n"
        "(Type 'skip' to skip this step)",
        parse_mode='Markdown'
    )
    return DESCRIPTION

async def topic_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    await update.message.reply_text(
        "📂 **Select a category** for your topic:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CATEGORY

async def topic_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the topic category."""
    query = update.callback_query
    await query.answer()
    
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
    
    await query.edit_message_text(
        f"✅ Category selected: *{category_map.get(category, category)}*\n\n"
        "📅 Now, set a **deadline** for your topic.\n"
        "(Format: YYYY-MM-DD or type 'skip' to skip)",
        parse_mode='Markdown'
    )
    return DEADLINE

async def topic_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the topic deadline and save the topic."""
    user_id = str(update.effective_user.id)
    deadline_input = update.message.text.strip()
    
    # Validate deadline format if not skipped
    deadline = None
    if deadline_input.lower() != 'skip':
        try:
            deadline = datetime.strptime(deadline_input, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            await update.message.reply_text(
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
    
    await update.message.reply_text(response, parse_mode='Markdown')
    return ConversationHandler.END

async def my_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all topics for the user."""
    user_id = str(update.effective_user.id)
    
    if user_id not in topics or not topics[user_id]:
        await update.message.reply_text(
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
    await update.message.reply_text(response, parse_mode='Markdown')

async def delete_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a topic."""
    user_id = str(update.effective_user.id)
    
    if user_id not in topics or not topics[user_id]:
        await update.message.reply_text(
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
    
    await update.message.reply_text(
        "🗑️ **Select a topic to delete:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    
    # Handle delete confirmation
    if data.startswith('del_'):
        if data == 'del_cancel':
            await query.edit_message_text("✅ Deletion cancelled.")
            return
        
        try:
            idx = int(data.replace('del_', ''))
            deleted_topic = topics[user_id].pop(idx)
            save_topics()
            
            await query.edit_message_text(
                f"✅ Topic deleted: *{deleted_topic['title']}*",
                parse_mode='Markdown'
            )
        except (IndexError, ValueError):
            await query.edit_message_text("❌ Error deleting topic. Please try again.")
    
    # Handle conversation category selection
    elif data.startswith('cat_'):
        # This is handled in topic_category function
        pass

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current conversation."""
    user_id = str(update.effective_user.id)
    if user_id in user_data_temp:
        del user_data_temp[user_id]
    
    await update.message.reply_text(
        "❌ Topic creation cancelled.\n"
        "Click /new to start again."
    )
    return ConversationHandler.END
