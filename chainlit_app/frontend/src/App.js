import React, { useState, useEffect } from 'react';
import TransactionForm from './components/TransactionForm';
import TransactionList from './components/TransactionList';
import Chat from './components/Chat';
import axios from 'axios';
import './App.css';

function App() {
  const [transactions, setTransactions] = useState([]);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const res = await axios.get('/transactions');
      setTransactions(res.data.data || []);
    } catch (err) {
      console.error('Failed to fetch transactions', err);
    }
  };

  const addTransaction = async (tx) => {
    try {
      await axios.post('/transactions', tx);
      fetchTransactions();
    } catch (err) {
      console.error('Failed to save transaction', err);
    }
  };

  return (
    <div className="App">
      <h1>Pocket CFO Dashboard</h1>
      <div className="main">
        <div className="left-pane">
          <TransactionForm onSubmit={addTransaction} />
          <TransactionList transactions={transactions} />
        </div>
        <div className="right-pane">
          <Chat />
        </div>
      </div>
    </div>
  );
}

export default App;