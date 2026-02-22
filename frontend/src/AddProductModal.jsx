import React, { useState, useRef } from 'react'
import { X, Save, Package, Image as ImageIcon, Camera } from 'lucide-react'
import axios from 'axios'

const API_BASE = "http://127.0.0.1:8000"

export default function AddProductModal({ onClose, onRefresh, notify }) {
    const [formData, setFormData] = useState({
        ean: '',
        ean_karton: '',
        nazwa_pl: '',
        nazwa_en: '',
        internal_id: '',
        kategoria: '',
        masa_netto: '',
        image_url: ''
    })
    const [loading, setLoading] = useState(false)
    const fileInputRef = useRef(null)

    const handleFileUpload = async (e) => {
        const file = e.target.files[0]
        if (!file) return

        const uploadData = new FormData()
        uploadData.append('file', file)

        try {
            setLoading(true)
            const res = await axios.post(`${API_BASE}/upload`, uploadData)
            setFormData({ ...formData, image_url: res.data.url })
            notify("Zdjęcie zostało przesłane!", "success")
        } catch (err) {
            notify("Błąd podczas przesyłania zdjęcia", "error")
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        try {
            await axios.post(`${API_BASE}/produkty`, { ...formData, skladniki: [] })
            notify("Wyrób został utworzony pomyślnie!", "success")
            onRefresh()
            onClose()
        } catch (err) {
            // Handled by global interceptor
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-choco-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white border border-choco-100 rounded-3xl w-full max-w-2xl shadow-2xl animate-in fade-in zoom-in duration-200 overflow-hidden">
                <div className="p-6 border-b border-choco-100 flex justify-between items-center bg-choco-50/50">
                    <div className="flex items-center gap-3">
                        <div className="bg-choco-800 p-2 rounded-lg shadow-lg">
                            <Package className="w-5 h-5 text-white" />
                        </div>
                        <h2 className="text-xl font-black text-choco-900 tracking-tight">Nowy Wyrób</h2>
                    </div>
                    <button onClick={onClose} className="text-choco-400 hover:text-choco-600 transition-colors p-2 hover:bg-white rounded-full">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-8 space-y-6 bg-white overflow-y-auto max-h-[80vh] custom-scrollbar">
                    <div className="grid grid-cols-3 gap-8">
                        {/* Image Upload Column */}
                        <div className="col-span-1">
                            <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-2">Zdjęcie Produktu</label>
                            <div
                                onClick={() => fileInputRef.current.click()}
                                className="aspect-[3/4] rounded-2xl border-2 border-dashed border-choco-100 bg-choco-50/30 flex flex-col items-center justify-center cursor-pointer hover:border-gold-500/50 hover:bg-choco-50 transition-all overflow-hidden group"
                            >
                                {formData.image_url ? (
                                    <img src={`${API_BASE}${formData.image_url}`} alt="Podgląd" className="w-full h-full object-cover" />
                                ) : (
                                    <>
                                        <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-choco-300 group-hover:text-gold-600 transition-colors shadow-sm mb-3">
                                            <Camera size={24} />
                                        </div>
                                        <span className="text-[10px] font-bold text-choco-400 uppercase tracking-widest">Wgraj zdjęcie</span>
                                    </>
                                )}
                            </div>
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileUpload}
                                className="hidden"
                                accept="image/*"
                            />
                        </div>

                        {/* Form Fields Column */}
                        <div className="col-span-2 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-1.5">EAN (Sztuka)</label>
                                    <input
                                        required
                                        type="text"
                                        maxLength={13}
                                        className="w-full bg-choco-50/50 border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all font-bold text-choco-900"
                                        value={formData.ean}
                                        onChange={(e) => setFormData({ ...formData, ean: e.target.value, internal_id: e.target.value.slice(-6) })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-1.5">EAN (Karton)</label>
                                    <input
                                        type="text"
                                        maxLength={13}
                                        className="w-full bg-choco-50/50 border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all font-bold text-choco-900"
                                        value={formData.ean_karton}
                                        onChange={(e) => setFormData({ ...formData, ean_karton: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-1.5">Nazwa Produktu (PL)</label>
                                <input
                                    required
                                    type="text"
                                    className="w-full bg-choco-50/50 border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all font-bold text-choco-900"
                                    value={formData.nazwa_pl}
                                    onChange={(e) => setFormData({ ...formData, nazwa_pl: e.target.value })}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-1.5">Kategoria</label>
                                    <input
                                        type="text"
                                        className="w-full bg-choco-50/50 border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all font-bold text-choco-900"
                                        value={formData.kategoria}
                                        onChange={(e) => setFormData({ ...formData, kategoria: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-1.5">Masa Netto (g)</label>
                                    <input
                                        type="text"
                                        className="w-full bg-choco-50/50 border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all font-bold text-choco-900"
                                        value={formData.masa_netto}
                                        onChange={(e) => setFormData({ ...formData, masa_netto: e.target.value })}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 flex gap-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-6 py-4 border border-choco-100 rounded-2xl font-black text-choco-500 hover:bg-choco-50 transition-all text-[10px] uppercase tracking-widest"
                        >
                            Anuluj
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-[2] bg-choco-800 hover:bg-choco-700 py-4 rounded-2xl font-black text-white shadow-xl shadow-choco-900/30 disabled:opacity-50 transition-all text-[10px] uppercase tracking-widest flex items-center justify-center gap-2"
                        >
                            {loading ? 'Przetwarzanie...' : <><Save size={16} /> Utwórz Wyrób</>}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
