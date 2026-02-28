import React from 'react';

function Chat() {
  // display the Chainlit interface via iframe
  return (
    <div className="chat-container">
      <h2>Chat</h2>
      <iframe
        title="Chainlit Chat"
        src="http://localhost:8001" // default Chainlit port; adjust if different
        style={{ width: '100%', height: '500px', border: '1px solid #ccc' }}
      />
    </div>
  );
}

export default Chat;