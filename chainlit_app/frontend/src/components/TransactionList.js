import React from 'react';

function TransactionList({ transactions }) {
  return (
    <div className="transaction-list">
      <h2>Recent Transactions</h2>
      {transactions.length === 0 && <p>No transactions yet.</p>}
      <ul>
        {transactions.map((tx) => (
          <li key={tx.id || tx.transaction_id}>
            <strong>{tx.description}</strong> — {tx.amount} ({tx.category})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default TransactionList;