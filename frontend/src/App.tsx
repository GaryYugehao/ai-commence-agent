import React, { useState, useEffect, useRef} from 'react';
import type { FormEvent } from 'react';
import axios from 'axios';

// Update this if your backend runs on a different port or if you use Ngrok
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8086';

interface Product {
    id: string;
    name: string;
    description: string;
    price: number;
    image_url: string;
    category: string;
    tags: string[];
}

interface MessageContent {
    type: 'user' | 'rufus';
    text: string;
    products?: Product[];
    isLoading?: boolean; // For Rufus's temporary thinking message
}

function App() {
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<MessageContent[]>([]);
    const [inputText, setInputText] = useState<string>('');
    const [isOverallLoading, setIsOverallLoading] = useState<boolean>(true); // For initial session start
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        const startNewSession = async () => {
            setIsOverallLoading(true);
            setError(null);
            try {
                const response = await axios.post(`${API_BASE_URL}/api/agent/start_session`, {
                    user_info: { source: "web_frontend" } // Optional user info
                });
                setSessionId(response.data.session_id);
                setMessages([{ type: 'rufus', text: response.data.initial_message }]);
            } catch (err) {
                console.error("Error starting session:", err);
                setError("Failed to connect with Rufus. Please ensure the backend is running and try refreshing.");
                setMessages([]); // Clear messages on critical error
            }
            setIsOverallLoading(false);
        };
        startNewSession();
    }, []);

    const addRufusThinkingMessage = () => {
        setMessages(prev => [...prev, { type: 'rufus', text: "Rufus is thinking...", isLoading: true }]);
    };

    const replaceRufusThinkingMessage = (newMessage: MessageContent) => {
        setMessages(prev => prev.map(m => m.isLoading ? newMessage : m));
    };

    const addRufusErrorMessage = (detail: string) => {
        const rufusError: MessageContent = { type: 'rufus', text: `Error: ${detail}` };
        setMessages(prev => prev.map(m => m.isLoading ? rufusError : m));
    }

    const handleSendMessage = async (e: FormEvent) => {
        e.preventDefault();
        if (!inputText.trim() || !sessionId) return;

        const currentInput = inputText;
        setInputText('');
        setMessages(prev => [...prev, { type: 'user', text: currentInput }]);
        addRufusThinkingMessage();

        try {
            // Heuristic: if user asks for recommendations, use the specific endpoint.
            // Otherwise, use the general chat endpoint.
            const lowerInput = currentInput.toLowerCase();
            let response;
            if (lowerInput.includes("recommend") || lowerInput.includes("find") || lowerInput.includes("search for") || lowerInput.includes("show me")) {
                response = await axios.post(`${API_BASE_URL}/api/agent/recommend-text`, { query: currentInput });
                replaceRufusThinkingMessage({
                    type: 'rufus',
                    text: response.data.message,
                    products: response.data.recommendations
                });
            } else {
                response = await axios.post(`${API_BASE_URL}/api/agent/chat`, {
                    session_id: sessionId,
                    message: currentInput,
                });
                replaceRufusThinkingMessage({ type: 'rufus', text: response.data.message });
            }
        } catch (err: any) {
            console.error("Error sending message:", err);
            const errorDetail = err.response?.data?.detail || "Failed to get a response from Rufus.";
            addRufusErrorMessage(errorDetail);
        }
    };

    const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !sessionId) return;

        setMessages(prev => [...prev, { type: 'user', text: `Looking for products similar to image: ${file.name}` }]);
        addRufusThinkingMessage();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post(`${API_BASE_URL}/api/agent/recommend-image`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            replaceRufusThinkingMessage({
                type: 'rufus',
                text: response.data.message,
                products: response.data.recommendations
            });
        } catch (err: any) {
            console.error("Error uploading image:", err);
            const errorDetail = err.response?.data?.detail || "Failed to get recommendations from image.";
            addRufusErrorMessage(errorDetail);
        } finally {
            if (fileInputRef.current) fileInputRef.current.value = ""; // Reset file input
        }
    };

    return (
        // PAGE WRAPPER: This div will have the overall page background and center the chatbox.
        <div className="min-h-screen bg-gradient-to-br from-slate-200 to-sky-200 flex flex-col items-center justify-center p-4 sm:p-6 md:p-8">

            {/* CHATBOX CARD CONTAINER */}
            <div className="w-full max-w-md sm:max-w-lg md:max-w-xl bg-white shadow-2xl rounded-xl flex flex-col overflow-hidden h-[70vh] … ">

                {/* Chatbox Header (same as before, ensure flex-shrink-0) */}
                <header className="bg-indigo-600 text-white p-3 sm:p-4 flex items-center space-x-3 shadow-md flex-shrink-0">
                    <img
                        src="https://ui-avatars.com/api/?name=R&background=FFFFFF&color=4F46E5&font-size=0.5&bold=true"
                        alt="Rufus Avatar"
                        className="w-8 h-8 sm:w-10 sm:h-10 rounded-full border-2 border-indigo-300"
                    />
                    <div>
                        <h1 className="text-lg sm:text-xl font-semibold tracking-tight">Rufus</h1>
                        <p className="text-xs text-indigo-200">Online</p> {/* Simplified status */}
                    </div>
                </header>

                {/* Loading and Error States (same as before, ensure they are inside the chatbox card) */}
                {isOverallLoading && (
                    <div className="flex-grow flex items-center justify-center p-4">
                        <p className="text-base sm:text-lg text-slate-500 animate-pulse">Initializing session...</p>
                    </div>
                )}
                {error && !isOverallLoading && (
                    <div className="flex-grow flex items-center justify-center p-4">
                        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 sm:p-4 rounded-md shadow" role="alert">
                            <p className="font-bold">Connection Error</p>
                            <p className="text-sm">{error}</p>
                        </div>
                    </div>
                )}

                {!isOverallLoading && !error && (
                    <>
                        {/* Messages Area (same as before, ensure messages-container class) */}
                        <main className="flex-grow overflow-y-auto p-3 sm:p-4 space-y-4 messages-container"> {/* Adjusted padding and spacing */}
                            {messages.map((msg, index) => (
                                <div key={index} className={`flex items-end space-x-2 ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    {/* Agent (Rufus) Avatar */}
                                    {msg.type === 'rufus' && (
                                        <img
                                            src="https://ui-avatars.com/api/?name=R&background=FFFFFF&color=4F46E5&font-size=0.5&bold=true"
                                            alt="Rufus"
                                            className="w-7 h-7 sm:w-8 sm:h-8 rounded-full self-start flex-shrink-0"
                                        />
                                    )}
                                    {/* Message Bubble */}
                                    <div
                                        className={`max-w-[70%] md:max-w-[65%] p-2.5 sm:p-3 shadow-md text-sm ${ // Adjusted padding
                                            msg.type === 'user'
                                                ? 'bg-indigo-500 text-white rounded-l-lg rounded-t-lg sm:rounded-l-xl sm:rounded-t-xl'
                                                : 'bg-slate-100 text-slate-800 rounded-r-lg rounded-t-lg sm:rounded-r-xl sm:rounded-t-xl'
                                        }`}
                                    >
                                        <p className="whitespace-pre-wrap break-words">
                                            {msg.isLoading ? (
                                                <span className="italic animate-pulse">{msg.text}</span>
                                            ) : (
                                                msg.text
                                            )}
                                        </p>
                                        {/* Product Display - Simplified for this view, your more detailed one can be used */}
                                        {msg.products && msg.products.length > 0 && !msg.isLoading && (
                                            <div className="mt-2 pt-2 border-t border-slate-300/50">
                                                <div className="grid grid-cols-1 gap-2"> {/* 确保产品列表有合适的布局容器 */}
                                                    {msg.products.slice(0, 3).map(product => (
                                                        <div key={product.id} className={`border rounded-lg p-2 flex items-center gap-2 ${msg.type === 'user' ? 'bg-indigo-400 border-indigo-300' : 'bg-white border-slate-300'}`}>
                                                            <img
                                                                src={`${API_BASE_URL}${product.image_url}`} // <-- 这是核心的修改！
                                                                alt={product.name}
                                                                className="w-12 h-12 object-cover rounded flex-shrink-0"
                                                                onError={(e) => { // 可选：添加一个错误处理，以防图片加载失败
                                                                    const target = e.target as HTMLImageElement;
                                                                    target.onerror = null; // 防止无限循环
                                                                    target.src = `https://placehold.co/60x60/E2E8F0/AAAAAA?text=Error`; // 备用图片
                                                                }}
                                                            />
                                                            <div>
                                                                <h5 className={`font-semibold text-xs ${msg.type === 'user' ? 'text-white' : 'text-indigo-700'}`}>{product.name}</h5>
                                                                <p className={`text-xs ${msg.type === 'user' ? 'text-indigo-100' : 'text-slate-600'}`}>${product.price.toFixed(2)}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                    {/* User Avatar */}
                                    {msg.type === 'user' && (
                                        <img
                                            src="https://ui-avatars.com/api/?name=U&background=E0E0E0&color=757575&font-size=0.5&bold=true"
                                            alt="User"
                                            className="w-7 h-7 sm:w-8 sm:h-8 rounded-full self-start flex-shrink-0"
                                        />
                                    )}
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </main>

                        {/* Chat Input Footer (ensure flex-shrink-0) */}
                        <footer className="bg-white p-2.5 sm:p-3 border-t border-slate-200 flex-shrink-0"> {/* Changed background to white for typical card style */}
                            <form onSubmit={handleSendMessage} className="flex items-center gap-2">
                                {/* Image Upload Button - Let's try a different SVG and ensure visibility */}
                                <label
                                    htmlFor="imageUploadInput"
                                    title="Attach image"
                                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-full cursor-pointer transition-colors flex-shrink-0"
                                >
                                    {/* Paperclip Icon (Common for attachments) */}
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 sm:w-6 sm:h-6">
                                        <path fillRule="evenodd" d="M15.621 4.379a3 3 0 00-4.242 0l-7 7a3 3 0 004.241 4.243h.001l.497-.5a.75.75 0 011.064 1.057l-.498.501-.002.002a4.5 4.5 0 01-6.364-6.364l7-7a4.5 4.5 0 016.368 6.36l-3.455 3.553A2.625 2.625 0 119.53 9.514l3.453-3.552a.75.75 0 011.061 1.06l-3.453 3.552 3.453 3.552a.75.75 0 01-1.06 1.061l-3.454-3.552a2.625 2.625 0 01-3.712-3.712l3.455-3.553-3.455-3.553A.75.75 0 015.879 4.38l3.454 3.552a4.125 4.125 0 005.832 5.832l3.455-3.553a3 3 0 000-4.242z" clipRule="evenodd" />
                                    </svg>
                                </label>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleImageUpload}
                                    accept="image/*"
                                    className="hidden"
                                    id="imageUploadInput"
                                    disabled={!sessionId || messages.some(m => m.isLoading)}
                                />
                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="Type a message..." // Simplified placeholder
                                    className="flex-grow p-2.5 sm:p-3 h-10 sm:h-11 border border-slate-300 rounded-full focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm"
                                />
                                <button
                                    type="submit"
                                    className="p-2 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 transition-colors disabled:bg-indigo-300 flex-shrink-0"
                                >
                                    {/* Send Icon SVG (same as before) */}
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 sm:w-6 sm:h-6">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                                    </svg>
                                </button>
                            </form>
                        </footer>
                    </>
                )}
            </div> {/* End CHATBOX CARD CONTAINER */}
        </div> // End PAGE WRAPPER
    );
}

export default App;