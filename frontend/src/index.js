import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './app/components/App';
import reportWebVitals from './hooks/reportWebVitals';

async function enableMocking() {
    if (process.env.REACT_APP_USE_MOCKS) {
        const { worker } = await import('./mocks/browser')

        // `worker.start()` returns a Promise that resolves
        // once the Service Worker is up and ready to intercept requests.
        return worker.start()
    }
}

enableMocking().then(() => {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
})
// If you want to start measuring performance in your flashcard_service, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
