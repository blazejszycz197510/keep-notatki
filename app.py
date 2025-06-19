from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

NOTES_FILE = 'notes.json'


def load_notes():
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_notes(notes):
    try:
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Błąd zapisu: {e}")


# HTML TEMPLATE - cała aplikacja w przeglądarce
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📝 Keep - Synchronizowane Notatki</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: #f5f5f5; 
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: #1976d2;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .container {
            display: flex;
            flex: 1;
            gap: 20px;
            padding: 20px;
            max-height: calc(100vh - 80px);
        }

        .notes-panel {
            width: 350px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }

        .notes-header {
            padding: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .notes-list {
            flex: 1;
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }

        .note-item {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
        }

        .note-item:hover { background: #f8f9fa; }
        .note-item.active { background: #e3f2fd; border-left: 4px solid #1976d2; }

        .note-title { 
            font-weight: bold; 
            margin-bottom: 4px;
            font-size: 14px;
        }

        .note-preview { 
            color: #666; 
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .editor-panel {
            flex: 1;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
        }

        .editor-header {
            padding: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            gap: 10px;
        }

        .editor-content {
            flex: 1;
            padding: 15px;
            display: flex;
            flex-direction: column;
        }

        .title-input {
            border: none;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
            padding: 8px;
            border-radius: 4px;
            background: #f8f9fa;
        }

        .content-textarea {
            flex: 1;
            border: none;
            resize: none;
            font-size: 14px;
            line-height: 1.5;
            padding: 8px;
            border-radius: 4px;
            background: #f8f9fa;
            min-height: 400px;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }

        .btn-primary { background: #1976d2; color: white; }
        .btn-primary:hover { background: #1565c0; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-secondary:hover { background: #5a6268; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-danger:hover { background: #c82333; }

        .status {
            padding: 10px 20px;
            background: #e8f5e8;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }

        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #999;
        }

        @media (max-width: 768px) {
            .container { flex-direction: column; }
            .notes-panel { width: 100%; max-height: 200px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📝 Keep - Synchronizowane Notatki</h1>
        <div>
            <span id="connection-status">🟢 Połączono</span>
            <span id="notes-count">Notatek: 0</span>
        </div>
    </div>

    <div class="container">
        <div class="notes-panel">
            <div class="notes-header">
                <h3>📋 Notatki</h3>
                <button class="btn btn-primary" onclick="createNote()">➕ Nowa</button>
            </div>
            <div class="notes-list" id="notes-list">
                <div class="empty-state">
                    <p>Brak notatek</p>
                    <p>Kliknij "➕ Nowa" aby utworzyć pierwszą notatkę</p>
                </div>
            </div>
        </div>

        <div class="editor-panel">
            <div class="editor-header">
                <button class="btn btn-primary" onclick="saveNote()">💾 Zapisz</button>
                <button class="btn btn-secondary" onclick="changeColor()">🎨 Kolor</button>
                <button class="btn btn-danger" onclick="deleteNote()">🗑️ Usuń</button>
                <input type="color" id="color-picker" style="display: none;" onchange="applyColor(this.value)">
            </div>
            <div class="editor-content" id="editor-content">
                <div class="empty-state">
                    <p>Wybierz notatkę do edycji</p>
                    <p>lub utwórz nową</p>
                </div>
            </div>
        </div>
    </div>

    <div class="status" id="status">Gotowy do pracy</div>

    <script>
        let notes = [];
        let currentNote = null;

        // Ładowanie notatek przy starcie
        document.addEventListener('DOMContentLoaded', function() {
            loadNotes();
            setInterval(loadNotes, 5000); // Odświeżaj co 5 sekund
        });

        async function loadNotes() {
            try {
                const response = await fetch('/api/notes');
                notes = await response.json();
                renderNotesList();
                updateStatus(`Załadowano ${notes.length} notatek`);
                document.getElementById('notes-count').textContent = `Notatek: ${notes.length}`;
            } catch (error) {
                updateStatus('❌ Błąd ładowania notatek');
                document.getElementById('connection-status').textContent = '🔴 Błąd połączenia';
            }
        }

        function renderNotesList() {
            const container = document.getElementById('notes-list');

            if (notes.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <p>Brak notatek</p>
                        <p>Kliknij "➕ Nowa" aby utworzyć pierwszą notatkę</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = notes.map(note => `
                <div class="note-item ${currentNote && currentNote.id === note.id ? 'active' : ''}" 
                     onclick="selectNote(${note.id})" 
                     style="border-left-color: ${note.color || '#1976d2'}">
                    <div class="note-title">${note.title || 'Bez tytułu'}</div>
                    <div class="note-preview">${note.content.substring(0, 50)}${note.content.length > 50 ? '...' : ''}</div>
                </div>
            `).join('');
        }

        function selectNote(noteId) {
            currentNote = notes.find(note => note.id === noteId);
            if (currentNote) {
                renderEditor();
                renderNotesList(); // Odśwież listę dla active state
                updateStatus(`Załadowano: ${currentNote.title}`);
            }
        }

        function renderEditor() {
            const container = document.getElementById('editor-content');
            const backgroundColor = currentNote.color || '#ffffff';

            container.innerHTML = `
                <input type="text" class="title-input" id="note-title" 
                       placeholder="Tytuł notatki..." 
                       value="${currentNote.title}" 
                       onkeyup="autoSave()" 
                       style="background-color: ${backgroundColor}">
                <textarea class="content-textarea" id="note-content" 
                          placeholder="Wpisz treść notatki..." 
                          onkeyup="autoSave()"
                          style="background-color: ${backgroundColor}">${currentNote.content}</textarea>
            `;
        }

        async function createNote() {
            const newNote = {
                title: 'Nowa notatka',
                content: '',
                color: '#ffffff'
            };

            try {
                const response = await fetch('/api/notes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newNote)
                });

                if (response.ok) {
                    const createdNote = await response.json();
                    notes.push(createdNote);
                    currentNote = createdNote;
                    renderNotesList();
                    renderEditor();
                    updateStatus('✅ Nowa notatka utworzona');

                    // Fokus na tytuł
                    setTimeout(() => {
                        document.getElementById('note-title').focus();
                        document.getElementById('note-title').select();
                    }, 100);
                }
            } catch (error) {
                updateStatus('❌ Błąd tworzenia notatki');
            }
        }

        async function saveNote() {
            if (!currentNote) {
                updateStatus('⚠️ Wybierz notatkę do zapisania');
                return;
            }

            const title = document.getElementById('note-title').value;
            const content = document.getElementById('note-content').value;

            const updatedNote = {
                title: title || 'Bez tytułu',
                content: content,
                color: currentNote.color || '#ffffff'
            };

            try {
                const response = await fetch(`/api/notes/${currentNote.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedNote)
                });

                if (response.ok) {
                    currentNote.title = updatedNote.title;
                    currentNote.content = updatedNote.content;
                    renderNotesList();
                    updateStatus('✅ Notatka zapisana');
                }
            } catch (error) {
                updateStatus('❌ Błąd zapisywania');
            }
        }

        async function deleteNote() {
            if (!currentNote) {
                updateStatus('⚠️ Wybierz notatkę do usunięcia');
                return;
            }

            if (confirm(`Czy na pewno chcesz usunąć notatkę "${currentNote.title}"?`)) {
                try {
                    const response = await fetch(`/api/notes/${currentNote.id}`, {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        notes = notes.filter(note => note.id !== currentNote.id);
                        currentNote = null;
                        renderNotesList();

                        document.getElementById('editor-content').innerHTML = `
                            <div class="empty-state">
                                <p>Wybierz notatkę do edycji</p>
                                <p>lub utwórz nową</p>
                            </div>
                        `;

                        updateStatus('✅ Notatka usunięta');
                    }
                } catch (error) {
                    updateStatus('❌ Błąd usuwania');
                }
            }
        }

        function changeColor() {
            if (!currentNote) {
                updateStatus('⚠️ Wybierz notatkę');
                return;
            }
            document.getElementById('color-picker').click();
        }

        async function applyColor(color) {
            if (!currentNote) return;

            currentNote.color = color;

            // Zastosuj kolor natychmiast
            document.getElementById('note-title').style.backgroundColor = color;
            document.getElementById('note-content').style.backgroundColor = color;

            // Zapisz automatycznie
            await saveNote();
        }

        let autoSaveTimer;
        function autoSave() {
            if (autoSaveTimer) clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(saveNote, 2000); // Auto-zapis po 2 sekundach
            updateStatus('Edytowanie... (automatyczny zapis za 2s)');
        }

        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
    </script>
</body>
</html>
'''


@app.route('/')
def home():
    """Główna strona aplikacji"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/notes', methods=['GET'])
def get_notes():
    """API: Pobiera wszystkie notatki"""
    return jsonify(load_notes())


@app.route('/api/notes', methods=['POST'])
def add_note():
    """API: Dodaje nową notatkę"""
    data = request.json
    notes = load_notes()

    max_id = max([note.get('id', 0) for note in notes], default=0)

    note = {
        'id': max_id + 1,
        'title': data.get('title', 'Nowa notatka'),
        'content': data.get('content', ''),
        'timestamp': datetime.now().isoformat(),
        'color': data.get('color', '#ffffff')
    }

    notes.append(note)
    save_notes(notes)
    return jsonify(note), 201


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """API: Aktualizuje notatkę"""
    data = request.json
    notes = load_notes()

    for note in notes:
        if note['id'] == note_id:
            note['title'] = data.get('title', note['title'])
            note['content'] = data.get('content', note['content'])
            note['color'] = data.get('color', note['color'])
            note['timestamp'] = datetime.now().isoformat()
            save_notes(notes)
            return jsonify(note)

    return jsonify({'error': 'Notatka nie znaleziona'}), 404


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """API: Usuwa notatkę"""
    notes = load_notes()
    original_count = len(notes)
    notes = [note for note in notes if note['id'] != note_id]

    if len(notes) < original_count:
        save_notes(notes)
        return jsonify({'message': 'Notatka usunięta'})
    else:
        return jsonify({'error': 'Notatka nie znaleziona'}), 404


if __name__ == '__main__':
    print("🚀 KEEP WEB SERVER")
    print("📍 Lokalnie: http://localhost:5000")
    print("🌐 W sieci: http://192.168.x.x:5000")
    print("⚡ Otwórz w przeglądarce!")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)