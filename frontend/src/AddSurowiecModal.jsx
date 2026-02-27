import React, { useState, useEffect } from 'react'
import { X, Plus, Trash2, RefreshCw } from 'lucide-react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || ""

export default function AddSurowiecModal({ onClose, onRefresh, notify, surowiec }) {
    // Initial state setup with JSON parsing for complex fields
    const getInitialData = () => {
        if (!surowiec) return {
            nazwa: '',
            kraj_pochodzenia: '',
            energia_kj: 0,
            energia_kcal: 0,
            tluszcz: 0,
            kwasy_nasycone: 0,
            weglowodany: 0,
            cukry: 0,
            bialko: 0,
            sol: 0,
            blonnik: 0,
            sklad_pl: '',
            alergen_gluten: 'Nie zawiera',
            alergen_skorupiaki: 'Nie zawiera',
            alergen_jaja: 'Nie zawiera',
            alergen_ryby: 'Nie zawiera',
            alergen_orzeszki_ziemne: 'Nie zawiera',
            alergen_soja: 'Nie zawiera',
            alergen_mleko: 'Nie zawiera',
            alergen_orzechy: 'Nie zawiera',
            alergen_seler: 'Nie zawiera',
            alergen_gorczyca: 'Nie zawiera',
            alergen_sezam: 'Nie zawiera',
            alergen_dwutlenek_siarki: 'Nie zawiera',
            alergen_lubin: 'Nie zawiera',
            alergen_mieczaki: 'Nie zawiera',
            sklad_procentowy: '[]',
            pochodzenie_skladnikow: '[]',
            kategoria: 'Inne'
        }

        return {
            ...surowiec,
            sklad_procentowy: surowiec.sklad_procentowy || '[]',
            pochodzenie_skladnikow: surowiec.pochodzenie_skladnikow || '[]',
            kategoria: surowiec.kategoria || 'Inne'
        }
    }

    const [formData, setFormData] = useState(getInitialData())
    const [loading, setLoading] = useState(false)
    const [activeSection, setActiveSection] = useState('osobowe')

    const [skladnikiProcenty, setSkladnikiProcenty] = useState([])
    const [skladnikiKraje, setSkladnikiKraje] = useState([])

    useEffect(() => {
        try {
            setSkladnikiProcenty(JSON.parse(formData.sklad_procentowy || '[]'))
            setSkladnikiKraje(JSON.parse(formData.pochodzenie_skladnikow || '[]'))
        } catch (e) {
            console.error("Error parsing JSON data", e)
            setSkladnikiProcenty([])
            setSkladnikiKraje([])
        }
    }, [surowiec])

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)

        const finalData = {
            ...formData,
            sklad_procentowy: JSON.stringify(skladnikiProcenty),
            pochodzenie_skladnikow: JSON.stringify(skladnikiKraje)
        }

        try {
            if (surowiec) {
                await axios.put(`${API_BASE}/surowce/${surowiec.id}`, finalData)
                notify("Surowiec został zaktualizowany!", "success")
            } else {
                await axios.post(`${API_BASE}/surowce`, finalData)
                notify("Surowiec został dodany pomyślnie!", "success")
            }
            onRefresh()
            onClose()
        } catch (err) {
            // Handled by global interceptor
        } finally {
            setLoading(false)
        }
    }

    const parseIngredientsFromText = () => {
        if (!formData.sklad_pl) return

        const items = formData.sklad_pl
            .split(/[,;]+/)
            .map(s => s.replace(/\s+/g, ' ').trim())
            .filter(s => s.length > 0 && !s.toLowerCase().includes('skład') && !s.toLowerCase().includes('składniki'))

        const newProcenty = items.map(name => {
            const existing = skladnikiProcenty.find(p => p.nazwa === name)
            return existing || { nazwa: name, procent: 0 }
        })
        setSkladnikiProcenty(newProcenty)

        const newKraje = items.map(name => {
            const existing = skladnikiKraje.find(k => k.nazwa === name)
            return existing || { nazwa: name, kraje: '' }
        })
        setSkladnikiKraje(newKraje)

        notify("Zsynchronizowano listę składników z opisu tekstowego", "info")
    }

    const allergenOptions = ["Nie zawiera", "Zawiera", "Może zawierać"]

    const addRowProcenty = () => setSkladnikiProcenty([...skladnikiProcenty, { nazwa: '', procent: 0 }])
    const removeRowProcenty = (index) => setSkladnikiProcenty(skladnikiProcenty.filter((_, i) => i !== index))
    const updateRowProcenty = (index, field, value) => {
        const updated = [...skladnikiProcenty]
        updated[index] = { ...updated[index], [field]: value }
        setSkladnikiProcenty(updated)
    }

    const addRowKraje = () => setSkladnikiKraje([...skladnikiKraje, { nazwa: '', kraje: '' }])
    const removeRowKraje = (index) => setSkladnikiKraje(skladnikiKraje.filter((_, i) => i !== index))
    const updateRowKraje = (index, field, value) => {
        const updated = [...skladnikiKraje]
        updated[index] = { ...updated[index], [field]: value }
        setSkladnikiKraje(updated)
    }

    return (
        <div className="fixed inset-0 bg-choco-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white border border-choco-100 rounded-3xl w-full max-w-4xl shadow-2xl animate-in fade-in zoom-in duration-200 overflow-hidden flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-choco-100 flex justify-between items-center bg-white">
                    <div>
                        <h2 className="text-xl font-black text-choco-900">{surowiec ? 'Edycja Surowca' : 'Nowy Surowiec'}</h2>
                        <p className="text-choco-500 text-[10px] uppercase font-bold tracking-widest mt-1">Strefa Produkcji | {formData.nazwa || 'Brak nazwy'}</p>
                    </div>
                    <button onClick={onClose} className="text-choco-400 hover:text-choco-500 transition-colors p-2 hover:bg-choco-50 rounded-full"><X /></button>
                </div>

                <div className="flex border-b border-choco-200 bg-choco-100/40 overflow-x-auto no-scrollbar shadow-sm">
                    {[
                        { id: 'osobowe', label: 'Dane Ogólne' },
                        { id: 'nutrition', label: 'Wartości Odżywcze' },
                        { id: 'procenty', label: 'Skład (%)' },
                        { id: 'allergens', label: 'Alergeny' },
                        { id: 'pochodzenie', label: 'Kraje pochodzenia' }
                    ].map(section => (
                        <button
                            key={section.id}
                            onClick={() => setActiveSection(section.id)}
                            className={`px-6 py-4 text-[11px] font-black uppercase tracking-wider transition-all whitespace-nowrap border-b-4 ${activeSection === section.id
                                ? 'text-choco-950 border-gold-500 bg-white'
                                : 'text-choco-800 border-transparent hover:text-choco-950 hover:bg-white/50'
                                }`}
                        >
                            {section.label}
                        </button>
                    ))}
                </div>

                <form id="surowiec-form" onSubmit={handleSubmit} className="p-8 overflow-y-auto flex-1 bg-white">
                    {activeSection === 'osobowe' && (
                        <div className="grid grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="col-span-2">
                                <label className="block text-[10px] font-black text-choco-500 uppercase tracking-widest mb-2">Pełna Nazwa Surowca (np. Polewa mleczna)</label>
                                <input
                                    required
                                    type="text"
                                    className="w-full bg-choco-50/50 border border-choco-100 rounded-2xl px-5 py-3.5 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all placeholder:text-choco-400 text-lg font-bold text-choco-900"
                                    value={formData.nazwa}
                                    onChange={(e) => setFormData({ ...formData, nazwa: e.target.value })}
                                />
                            </div>
                            <div className="col-span-2 md:col-span-1">
                                <label className="block text-[10px] font-black text-choco-500 uppercase tracking-widest mb-2">Kategoria</label>
                                <input
                                    type="text"
                                    className="w-full bg-choco-50/50 border border-choco-100 rounded-2xl px-5 py-3.5 focus:ring-4 focus:ring-choco-100/50 outline-none transition-all placeholder:text-choco-400 font-bold text-choco-900"
                                    value={formData.kategoria}
                                    onChange={(e) => setFormData({ ...formData, kategoria: e.target.value })}
                                    placeholder="np. Master Martini"
                                />
                            </div>
                            <div className="col-span-2">
                                <div className="flex justify-between items-center mb-2">
                                    <label className="block text-[10px] font-black text-choco-500 uppercase tracking-widest">Pełny Opis Składników (ze zdjęcia)</label>
                                    <button
                                        type="button"
                                        onClick={parseIngredientsFromText}
                                        className="text-[10px] font-bold bg-gold-600/10 text-gold-600 px-4 py-1.5 rounded-full hover:bg-gold-600/20 flex items-center gap-2 border border-gold-600/20 transition-all font-sans"
                                    >
                                        <RefreshCw size={10} /> Pobierz listę składników
                                    </button>
                                </div>
                                <textarea
                                    className="w-full bg-choco-50/50 border border-choco-100 rounded-2xl px-5 py-4 focus:ring-4 focus:ring-choco-100/50 outline-none h-40 resize-none font-medium text-choco-700 leading-relaxed placeholder:text-choco-400"
                                    value={formData.sklad_pl}
                                    onChange={(e) => setFormData({ ...formData, sklad_pl: e.target.value })}
                                    placeholder="Wklej tutaj listę składników..."
                                />
                                <p className="text-[9px] text-choco-500 mt-2 uppercase tracking-wide font-bold">WSKAZÓWKA: KLIKNIJ PRZYCISK POWYŻEJ, ABY WYGENEROWAĆ TABELE PROCENTÓW I KRAJÓW.</p>
                            </div>
                        </div>
                    )}

                    {activeSection === 'procenty' && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-black text-choco-800 uppercase tracking-widest">Składniki Procentowo (%)</h3>
                                <button type="button" onClick={addRowProcenty} className="bg-choco-50 hover:bg-choco-100 p-2.5 rounded-xl text-choco-600"><Plus size={18} /></button>
                            </div>
                            <div className="space-y-3">
                                {skladnikiProcenty.length === 0 && (
                                    <div className="text-center py-16 border-2 border-dashed border-choco-100 rounded-3xl text-choco-400 font-bold uppercase text-[10px] tracking-widest">
                                        Brak składników. Użyj synchronizacji w Dane Ogólne.
                                    </div>
                                )}
                                {skladnikiProcenty.map((item, idx) => (
                                    <div key={idx} className="flex gap-4 items-center p-3 bg-choco-50/30 rounded-2xl border border-choco-100/50 animate-in slide-in-from-left-2 duration-200" style={{ animationDelay: `${idx * 30}ms` }}>
                                        <input
                                            type="text"
                                            placeholder="Nazwa składnika"
                                            className="flex-1 bg-white border border-choco-100 rounded-xl px-5 py-3 text-sm font-bold text-choco-800"
                                            value={item.nazwa}
                                            onChange={(e) => updateRowProcenty(idx, 'nazwa', e.target.value)}
                                        />
                                        <div className="w-32 relative">
                                            <input
                                                type="number"
                                                step="0.01"
                                                className="w-full bg-white border border-choco-100 rounded-xl px-4 py-3 text-sm text-right pr-10 font-black text-choco-700"
                                                value={item.procent}
                                                onChange={(e) => updateRowProcenty(idx, 'procent', parseFloat(e.target.value) || 0)}
                                            />
                                            <span className="absolute right-4 top-3 text-choco-400 text-sm font-bold">%</span>
                                        </div>
                                        <button type="button" onClick={() => removeRowProcenty(idx)} className="text-choco-400 hover:text-red-500 transition-colors p-2"><Trash2 size={18} /></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeSection === 'pochodzenie' && (
                        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-black text-choco-800 uppercase tracking-widest">Kraje pochodzenia składników</h3>
                                <button type="button" onClick={addRowKraje} className="bg-choco-50 hover:bg-choco-100 p-2.5 rounded-xl text-choco-600 transition-all"><Plus size={18} /></button>
                            </div>
                            <div className="space-y-3">
                                {skladnikiKraje.length === 0 && (
                                    <div className="text-center py-16 border-2 border-dashed border-choco-100 rounded-3xl text-choco-400 font-bold uppercase text-[10px] tracking-widest">
                                        Brak składników. Użyj synchronizacji w Dane Ogólne.
                                    </div>
                                )}
                                {skladnikiKraje.map((item, idx) => (
                                    <div key={idx} className="flex gap-4 items-center p-3 bg-choco-50/30 rounded-2xl border border-choco-100/50 animate-in slide-in-from-left-2 duration-200" style={{ animationDelay: `${idx * 30}ms` }}>
                                        <input
                                            type="text"
                                            className="w-1/3 bg-white border border-choco-100 rounded-xl px-5 py-3 text-sm font-bold text-choco-700"
                                            value={item.nazwa}
                                            onChange={(e) => updateRowKraje(idx, 'nazwa', e.target.value)}
                                            placeholder="Składnik"
                                        />
                                        <input
                                            type="text"
                                            className="flex-1 bg-white border border-choco-100 rounded-xl px-5 py-3 text-sm font-bold text-choco-800"
                                            value={item.kraje}
                                            onChange={(e) => updateRowKraje(idx, 'kraje', e.target.value)}
                                            placeholder="Kraje pochodzenia (np. UE, Brazylia, Polska)"
                                        />
                                        <button type="button" onClick={() => removeRowKraje(idx)} className="text-choco-400 hover:text-red-500 transition-colors p-2"><Trash2 size={18} /></button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeSection === 'nutrition' && (
                        <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {[
                                { label: 'Energia (kJ)', key: 'energia_kj' },
                                { label: 'Energia (kcal)', key: 'energia_kcal' },
                                { label: 'Tłuszcz (g)', key: 'tluszcz' },
                                { label: 'Kwasy Nasycone (g)', key: 'kwasy_nasycone' },
                                { label: 'Węglowodany (g)', key: 'weglowodany' },
                                { label: 'Cukry (g)', key: 'cukry' },
                                { label: 'Białko (g)', key: 'bialko' },
                                { label: 'Sól (g)', key: 'sol' },
                                { label: 'Błonnik (g)', key: 'blonnik' }
                            ].map(field => (
                                <div key={field.key} className="bg-choco-50/50 p-4 rounded-2xl border border-choco-100/50 group hover:border-choco-400 transition-all">
                                    <label className="block text-[10px] font-black text-choco-600 uppercase tracking-widest mb-2">{field.label}</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        className="w-full bg-white border border-choco-100 rounded-xl px-4 py-3 focus:ring-4 focus:ring-choco-100/30 outline-none font-bold text-center text-choco-800"
                                        value={formData[field.key]}
                                        onChange={(e) => setFormData({ ...formData, [field.key]: parseFloat(e.target.value) || 0 })}
                                    />
                                </div>
                            ))}
                        </div>
                    )}

                    {activeSection === 'allergens' && (
                        <div className="grid grid-cols-2 gap-x-8 gap-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            {[
                                'gluten', 'skorupiaki', 'jaja', 'ryby', 'orzeszki_ziemne',
                                'soja', 'mleko', 'orzechy', 'seler', 'gorczyca',
                                'sezam', 'dwutlenek_siarki', 'lubin', 'mieczaki'
                            ].map(alg => (
                                <div key={alg} className="flex justify-between items-center p-4 bg-choco-50/50 rounded-2xl border border-choco-100/50">
                                    <span className="text-[10px] font-black text-choco-700 uppercase tracking-widest">{alg.replace('_', ' ')}</span>
                                    <select
                                        className={`bg-white border rounded-xl px-4 py-2 text-xs font-bold outline-none transition-all ${formData[`alergen_${alg}`] === 'Zawiera' ? 'border-red-500 text-red-600 bg-red-50' :
                                            formData[`alergen_${alg}`] === 'Może zawierać' ? 'border-gold-500 text-gold-600 bg-gold-50' :
                                                formData[`alergen_${alg}`] === 'Nie zawiera' ? 'border-green-500 text-green-600 bg-green-50' :
                                                    'border-choco-200 text-choco-800'
                                            }`}
                                        value={formData[`alergen_${alg}`]}
                                        onChange={(e) => setFormData({ ...formData, [`alergen_${alg}`]: e.target.value })}
                                    >
                                        {allergenOptions.map(opt => <option key={opt} value={opt} className="bg-white text-choco-800">{opt}</option>)}
                                    </select>
                                </div>
                            ))}
                        </div>
                    )}
                </form>

                <div className="p-8 border-t border-choco-100 bg-white flex gap-6">
                    <button
                        type="button"
                        onClick={onClose}
                        className="flex-1 px-6 py-4 border border-choco-100 rounded-2xl font-black text-choco-500 hover:bg-choco-50 transition-all text-[10px] uppercase tracking-widest"
                    >
                        Anuluj
                    </button>
                    <button
                        form="surowiec-form"
                        type="submit"
                        disabled={loading}
                        className="flex-[2] bg-choco-800 hover:bg-choco-700 py-4 rounded-2xl font-black text-white shadow-xl shadow-choco-900/20 disabled:opacity-50 transition-all text-[10px] uppercase tracking-widest"
                    >
                        {loading ? 'Przetwarzanie...' : (surowiec ? 'Zapisz Specyfikację' : 'Dodaj Surowiec')}
                    </button>
                </div>
            </div>
        </div>
    )
}
