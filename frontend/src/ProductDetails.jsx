import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import {
    X,
    Save,
    FileDown,
    Trash2,
    Plus,
    Info,
    ChevronDown,
    ChevronUp,
    AlertCircle,
    Cloud,
    Camera,
    Image as ImageIcon
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE || ""

// ---------------------------------------------------------------------------
// Allergen auto-bolding
// ---------------------------------------------------------------------------
const _PL_CHARS = 'a-zA-ZąęóśźżćńłĄĘÓŚŹŻĆŃŁ'

const _ALLERGEN_BOLD_WORDS = [
    // Multi-word phrases first (longest → shortest prevents partial overlap)
    'orzeszki arachidowe',
    'orzechy laskowe',
    // Single words
    'mleko', 'mleka', 'mleczne', 'mleczny',
    'soja', 'soi', 'sojowa', 'sojowe',
    'gluten', 'pszenna',
    'jaja', 'jaj',
    'orzechy', 'migdały', 'pistacje', 'pisatacje',
    'sezam',
]

const _allergenPattern = new RegExp(
    `(?<![${_PL_CHARS}])(${[..._ALLERGEN_BOLD_WORDS]
        .sort((a, b) => b.length - a.length)
        .map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('|')})(?![${_PL_CHARS}])`,
    'gi'
)

function _escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
}

function boldAllergens(text) {
    if (!text) return ''
    return _escapeHtml(text).replace(_allergenPattern, '<strong>$1</strong>')
}

export default function ProductDetails({ ean, onClose, notify, onRefresh }) {
    const [product, setProduct] = useState(null)
    const [initialProduct, setInitialProduct] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [activeTab, setActiveTab] = useState('dane_ogolne')
    const [availableSurowce, setAvailableSurowce] = useState([])
    const [showAddMenu, setShowAddMenu] = useState(false)
    const [suggestions, setSuggestions] = useState({})
    const userChangedInputRef = useRef(false)
    const palletHeightChangedRef = useRef(false)

    const isDirty = () => {
        return JSON.stringify(product) !== JSON.stringify(initialProduct)
    }

    const handleTabChange = (newTab) => {
        if (isDirty()) {
            if (window.confirm("Masz niezapisane zmiany. Czy na pewno chcesz zmienić zakładkę?")) {
                setActiveTab(newTab)
            }
        } else {
            setActiveTab(newTab)
        }
    }

    const fetchSuggestions = async (field, q, recent = false) => {
        try {
            const params = { field, q, recent }
            if (product?.ean) params.current_ean = product.ean
            const res = await axios.get(`${API_BASE}/produkty/sugestie/organoleptyka`, { params })
            setSuggestions(prev => ({ ...prev, [field]: res.data }))
        } catch (err) {
            console.error("Error fetching suggestions:", err)
        }
    }

    useEffect(() => {
        fetchData()
    }, [ean])

    useEffect(() => {
        if (!userChangedInputRef.current) return
        userChangedInputRef.current = false
        setProduct(prev => {
            if (!prev) return prev
            const sztuki = prev.logistyka_sztuk_w_zbiorczym
            const kartony = prev.logistyka_kartonow_na_warstwie
            const warstwy = prev.logistyka_warstw_na_palecie
            const hasVal = (v) => v != null && v !== ''
            return {
                ...prev,
                logistyka_sztuk_na_warstwie: (hasVal(sztuki) && hasVal(kartony))
                    ? Math.trunc(Number(sztuki) * Number(kartony)) : null,
                logistyka_kartonow_na_palecie: (hasVal(kartony) && hasVal(warstwy))
                    ? Math.trunc(Number(kartony) * Number(warstwy)) : null,
                logistyka_sztuk_na_palecie: (hasVal(sztuki) && hasVal(kartony) && hasVal(warstwy))
                    ? Math.trunc(Number(sztuki) * Number(kartony) * Number(warstwy)) : null,
            }
        })
    }, [product?.logistyka_sztuk_w_zbiorczym, product?.logistyka_kartonow_na_warstwie, product?.logistyka_warstw_na_palecie])

    useEffect(() => {
        if (!palletHeightChangedRef.current) return
        palletHeightChangedRef.current = false
        setProduct(prev => {
            if (!prev) return prev
            const warstwy = prev.logistyka_warstw_na_palecie
            const h1 = prev.logistyka_wymiary_zbiorcze1_h
            const h2 = prev.logistyka_wymiary_zbiorcze2_h
            const h3 = prev.logistyka_wymiary_zbiorcze3_h
            const hasVal = (v) => v != null && v !== '' && Number(v) > 0
            let selectedHeight = null
            if (hasVal(h3)) selectedHeight = Number(h3)
            else if (hasVal(h2)) selectedHeight = Number(h2)
            else if (hasVal(h1)) selectedHeight = Number(h1)
            if (!hasVal(warstwy) || selectedHeight === null) {
                return { ...prev, logistyka_wysokosc_palety: null }
            }
            return {
                ...prev,
                logistyka_wysokosc_palety: Number(warstwy) * selectedHeight + 15,
            }
        })
    }, [product?.logistyka_warstw_na_palecie, product?.logistyka_wymiary_zbiorcze1_h, product?.logistyka_wymiary_zbiorcze2_h, product?.logistyka_wymiary_zbiorcze3_h])

    const fetchData = async () => {
        setLoading(true)
        try {
            const [prodRes, analRes, surRes] = await Promise.all([
                axios.get(`${API_BASE}/produkty/${ean}`),
                axios.get(`${API_BASE}/produkty/${ean}/analiza`),
                axios.get(`${API_BASE}/surowce/`)
            ])
            setProduct(prodRes.data)
            setInitialProduct(prodRes.data)
            setAnalysis(analRes.data)
            setAvailableSurowce(surRes.data)
        } catch (err) {
            console.error("Error fetching product data:", err)
        } finally {
            setLoading(false)
        }
    }

    const updateSkladnikProcent = (index, value) => {
        const normalizedValue = typeof value === 'string' ? value.replace(',', '.') : value
        const updatedSkladniki = [...product.skladniki]
        updatedSkladniki[index] = { ...updatedSkladniki[index], procent: parseFloat(normalizedValue) || 0 }
        setProduct({ ...product, skladniki: updatedSkladniki })
    }

    const removeSkladnik = (index) => {
        const updatedSkladniki = product.skladniki.filter((_, i) => i !== index)
        setProduct({ ...product, skladniki: updatedSkladniki })
    }

    const addSkladnik = (surowiec) => {
        const newSkladnik = {
            surowiec_id: surowiec.id,
            surowiec: surowiec,
            procent: 0,
            kolejnosc: product.skladniki.length + 1
        }
        setProduct({ ...product, skladniki: [...product.skladniki, newSkladnik] })
        setShowAddMenu(false)
    }

    const handleDownload = async (lang = 'pl') => {
        try {
            const response = await axios({
                url: `${API_BASE}/produkty/${ean}/download?lang=${lang}`,
                method: 'GET',
                responseType: 'blob',
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `Karta_Produktu_${ean}_${lang}.xlsx`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            notify(`Pobieranie karty (${lang.toUpperCase()}) rozpoczęte`, 'success')
        } catch (err) {
            // Global interceptor handles the notification
        }
    }

    const handleDownloadPDF = async () => {
        try {
            const response = await axios({
                url: `${API_BASE}/produkty/${ean}/pdf`,
                method: 'GET',
                responseType: 'blob',
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `Specyfikacja_${ean}.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            notify('Pobieranie specyfikacji PDF rozpoczęte', 'success')
        } catch (err) {
            // Error handled by global interceptor
        }
    }

    const handleDownloadPDFEn = async () => {
        try {
            const response = await axios({
                url: `${API_BASE}/produkty/${ean}/pdf?lang=en`,
                method: 'GET',
                responseType: 'blob',
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', `Specyfikacja_${ean}_EN.pdf`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            notify('Downloading EN PDF specification...', 'success')
        } catch (err) {
            // Error handled by global interceptor
        }
    }

    const handleDownloadExcelEn = async () => {
        try {
            const response = await axios({
                url: `${API_BASE}/produkty/${ean}/download?lang=en`,
                method: 'GET',
                responseType: 'blob',
            })
            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            const safeName = (product?.nazwa_pl || ean)
                .replace(/[^\w\sąęóśźżćńłĄĘÓŚŹŻĆŃŁ-]/g, '')
                .trim()
                .replace(/\s+/g, '-')
            link.setAttribute('download', `${safeName}_EN.xlsx`)
            document.body.appendChild(link)
            link.click()
            link.remove()
            notify('Pobieranie karty EN (XLSX) rozpoczęte', 'success')
        } catch (err) {
            // Global interceptor handles the notification
        }
    }

    const handleSharePointSync = async (lang = 'pl') => {
        try {
            const folder = prompt("Podaj folder na SharePoint (np. /sites/Marketing/Shared Documents/Karty):", "/Shared Documents")
            if (!folder) return

            setSaving(true)
            await axios.post(`${API_BASE}/produkty/${ean}/sharepoint?lang=${lang}&folder=${folder}`)
            notify("Pomyślnie przesłano do SharePoint!", 'success')
        } catch (err) {
            // Global interceptor handles error
        } finally {
            setSaving(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            const payload = {
                ean: product.ean,
                ean_karton: product.ean_karton,
                nazwa_pl: product.nazwa_pl,
                nazwa_en: product.nazwa_en,
                internal_id: product.internal_id,
                prawna_nazwa_pl: product.prawna_nazwa_pl,
                prawna_nazwa_en: product.prawna_nazwa_en,
                kategoria: product.kategoria,
                product_type: product.product_type || 'inne',
                masa_netto: product.masa_netto,
                image_url: product.image_url,
                skladniki: product.skladniki.map(s => ({
                    surowiec_id: s.surowiec_id,
                    procent: s.procent,
                    kolejnosc: s.kolejnosc
                })),
                organoleptyka_smak: product.organoleptyka_smak,
                organoleptyka_zapach: product.organoleptyka_zapach,
                organoleptyka_kolor: product.organoleptyka_kolor,
                organoleptyka_wyglad_zewnetrzny: product.organoleptyka_wyglad_zewnetrzny,
                organoleptyka_wyglad_na_przekroju: product.organoleptyka_wyglad_na_przekroju,
                warunki_przechowywania: product.warunki_przechowywania,
                termin_przydatnosci: product.termin_przydatnosci,
                wyrazenie_format_daty: product.wyrazenie_format_daty,
                informacje_dodatkowe: product.informacje_dodatkowe,
                kod_cn: product.kod_cn,
                kod_pkwiu: product.kod_pkwiu,
                certyfikaty: typeof product.certyfikaty === 'string' ? product.certyfikaty : JSON.stringify(product.certyfikaty || []),
                logistyka_wymiary_solo_h: product.logistyka_wymiary_solo_h,
                logistyka_wymiary_solo_w: product.logistyka_wymiary_solo_w,
                logistyka_wymiary_solo_d: product.logistyka_wymiary_solo_d,
                logistyka_wymiary_jednostka_h: product.logistyka_wymiary_jednostka_h,
                logistyka_wymiary_jednostka_w: product.logistyka_wymiary_jednostka_w,
                logistyka_wymiary_jednostka_d: product.logistyka_wymiary_jednostka_d,
                logistyka_wymiary_zbiorcze1_h: product.logistyka_wymiary_zbiorcze1_h,
                logistyka_wymiary_zbiorcze1_w: product.logistyka_wymiary_zbiorcze1_w,
                logistyka_wymiary_zbiorcze1_d: product.logistyka_wymiary_zbiorcze1_d,
                logistyka_wymiary_zbiorcze2_h: product.logistyka_wymiary_zbiorcze2_h,
                logistyka_wymiary_zbiorcze2_w: product.logistyka_wymiary_zbiorcze2_w,
                logistyka_wymiary_zbiorcze2_d: product.logistyka_wymiary_zbiorcze2_d,
                logistyka_wymiary_zbiorcze3_h: product.logistyka_wymiary_zbiorcze3_h,
                logistyka_wymiary_zbiorcze3_w: product.logistyka_wymiary_zbiorcze3_w,
                logistyka_wymiary_zbiorcze3_d: product.logistyka_wymiary_zbiorcze3_d,
                logistyka_rodzaj_palety: product.logistyka_rodzaj_palety,
                logistyka_waga_netto_szt: product.logistyka_waga_netto_szt,
                logistyka_waga_brutto_szt: product.logistyka_waga_brutto_szt,
                logistyka_waga_netto_zbiorcze: product.logistyka_waga_netto_zbiorcze,
                logistyka_waga_brutto_zbiorcze: product.logistyka_waga_brutto_zbiorcze,
                logistyka_waga_netto_paleta: product.logistyka_waga_netto_paleta,
                logistyka_waga_brutto_paleta: product.logistyka_waga_brutto_paleta,
                logistyka_sztuk_w_zbiorczym: product.logistyka_sztuk_w_zbiorczym,
                logistyka_kartonow_na_warstwie: product.logistyka_kartonow_na_warstwie,
                logistyka_warstw_na_palecie: product.logistyka_warstw_na_palecie,
                logistyka_kartonow_na_palecie: product.logistyka_kartonow_na_palecie,
                logistyka_sztuk_na_palecie: product.logistyka_sztuk_na_palecie,
                logistyka_sztuk_na_warstwie: product.logistyka_sztuk_na_warstwie,
                logistyka_wysokosc_palety: product.logistyka_wysokosc_palety
            }
            await axios.put(`${API_BASE}/produkty/${ean}`, payload)
            notify("Zmiany zostały zapisane pomyślnie!", 'success')
            setInitialProduct(product) // Sync initial state after successful save
            fetchData() // Refresh local data
            if (onRefresh) onRefresh() // Refresh main list
        } catch (err) {
            // Global interceptor handles error
        } finally {
            setSaving(false)
        }
    }

    // Live Nutrition Calculation
    const liveNutrition = product ? (() => {
        const nutrition = {
            energia_kj: 0,
            energia_kcal: 0,
            tluszcz: 0,
            kwasy_nasycone: 0,
            weglowodany: 0,
            cukry: 0,
            bialko: 0,
            sol: 0,
            blonnik: 0
        };

        product.skladniki.forEach(sk => {
            const factor = sk.procent / 100.0;
            const sur = sk.surowiec;
            if (sur) {
                nutrition.energia_kj += (sur.energia_kj || 0) * factor;
                nutrition.energia_kcal += (sur.energia_kcal || 0) * factor;
                nutrition.tluszcz += (sur.tluszcz || 0) * factor;
                nutrition.kwasy_nasycone += (sur.kwasy_nasycone || 0) * factor;
                nutrition.weglowodany += (sur.weglowodany || 0) * factor;
                nutrition.cukry += (sur.cukry || 0) * factor;
                nutrition.bialko += (sur.bialko || 0) * factor;
                nutrition.sol += (sur.sol || 0) * factor;
                nutrition.blonnik += (sur.blonnik || 0) * factor;
            }
        });
        return nutrition;
    })() : null;

    const nutritionLabels = {
        energia_kj: "Energia Kj:",
        energia_kcal: "Energia Kcal:",
        tluszcz: "Tluszcz:",
        kwasy_nasycone: "Kwasy Nasycone:",
        weglowodany: "Weglowodany:",
        cukry: "Cukry:",
        bialko: "Bialko:",
        sol: "Sól:",
        blonnik: "Błonnik:"
    };

    if (loading) return (
        <div className="fixed inset-0 bg-choco-900/60 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-choco-400"></div>
        </div>
    )

    if (!product) return null

    return (
        <div className="fixed inset-0 bg-choco-900/60 backdrop-blur-sm z-50 flex items-center justify-end">
            <div className="w-[800px] h-full bg-choco-50 border-l border-choco-100 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
                {/* Header Section (Fixed) */}
                <div className="bg-white border-b border-choco-100 z-10">
                    {/* Main Header */}
                    <div className="p-8 flex items-start gap-8">
                        <div
                            onClick={() => document.getElementById('image-upload').click()}
                            className="w-32 h-32 rounded-2xl bg-choco-50 border border-choco-100 overflow-hidden group cursor-pointer relative shadow-md shrink-0"
                        >
                            {product.image_url ? (
                                <img src={product.image_url.startsWith('http') ? product.image_url : `${API_BASE}${product.image_url}`} alt={product.nazwa_pl} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center text-choco-300">
                                    <Camera size={32} />
                                    <span className="text-[8px] font-black uppercase mt-1">Dodaj foto</span>
                                </div>
                            )}
                            <div className="absolute inset-0 bg-choco-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                <Camera className="text-white w-8 h-8" />
                            </div>
                            <input
                                id="image-upload"
                                type="file"
                                className="hidden"
                                onChange={async (e) => {
                                    const file = e.target.files[0]
                                    if (!file) return
                                    const formData = new FormData()
                                    formData.append('file', file)
                                    try {
                                        const res = await axios.post(`${API_BASE}/upload`, formData)
                                        const newUrl = res.data.url
                                        setProduct({ ...product, image_url: newUrl })
                                        // Auto-save image_url immediately so it persists without requiring Save
                                        await axios.patch(`${API_BASE}/produkty/${product.ean}/image`, { image_url: newUrl })
                                        notify("Zdjęcie zaktualizowane i zapisane!", "success")
                                    } catch (err) {
                                        notify("Błąd przesyłania", "error")
                                    }
                                }}
                            />
                        </div>

                        <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-start gap-3">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 text-gold-600 text-[10px] font-black uppercase tracking-[0.2em] mb-2">
                                        <Info className="w-3 h-3" />
                                        Specyfikacja Wyrobu
                                    </div>
                                    <textarea
                                        value={product.nazwa_pl || ''}
                                        onChange={(e) => setProduct({ ...product, nazwa_pl: e.target.value })}
                                        className="text-xl font-black text-choco-900 leading-tight uppercase tracking-tight bg-transparent border-b-2 border-transparent focus:border-gold-500 focus:outline-none transition-colors w-full resize-none"
                                        style={{ wordBreak: 'break-word', overflowWrap: 'anywhere', fieldSizing: 'content', overflow: 'hidden' }}
                                        rows={1}
                                        placeholder="Nazwa wyrobu..."
                                    />
                                    <div className="flex flex-nowrap gap-3 mt-0 items-stretch">
                                        <div className="bg-choco-50 px-3 py-2 rounded-2xl border border-choco-100 flex flex-col group/input focus-within:ring-2 focus-within:ring-gold-500/20 transition-all">
                                            <span className="text-[8px] font-black text-choco-400 uppercase tracking-widest mb-1 whitespace-nowrap">EAN Sztuka (Główny)</span>
                                            <input
                                                type="text"
                                                value={product.ean}
                                                onChange={(e) => setProduct({ ...product, ean: e.target.value })}
                                                className="bg-transparent text-sm font-bold text-choco-900 focus:outline-none w-28"
                                                placeholder="590..."
                                            />
                                        </div>
                                        <div className="bg-choco-50 px-3 py-2 rounded-2xl border border-choco-100 flex flex-col group/input focus-within:ring-2 focus-within:ring-gold-500/20 transition-all">
                                            <span className="text-[8px] font-black text-choco-400 uppercase tracking-widest mb-1 whitespace-nowrap">EAN Karton</span>
                                            <input
                                                type="text"
                                                value={product.ean_karton || ''}
                                                onChange={(e) => setProduct({ ...product, ean_karton: e.target.value })}
                                                className="bg-transparent text-sm font-bold text-choco-900 focus:outline-none w-28"
                                                placeholder="590..."
                                            />
                                        </div>
                                        <div className="bg-choco-100/30 px-3 py-2 rounded-2xl border border-dashed border-choco-200 flex flex-col opacity-60">
                                            <span className="text-[8px] font-black text-choco-400 uppercase tracking-widest mb-1 whitespace-nowrap">Kod ID (Auto)</span>
                                            <span className="text-sm font-bold text-choco-600 font-mono">{product.ean.slice(-6)}</span>
                                        </div>
                                        <div className="bg-choco-50 px-3 py-2 rounded-2xl border border-choco-100 flex flex-col group/input focus-within:ring-2 focus-within:ring-gold-500/20 transition-all">
                                            <span className="text-[8px] font-black text-choco-400 uppercase tracking-widest mb-1 whitespace-nowrap">Kategoria</span>
                                            <select
                                                value={product.kategoria || ''}
                                                onChange={(e) => setProduct({ ...product, kategoria: e.target.value })}
                                                className="bg-transparent text-sm font-bold text-choco-900 focus:outline-none cursor-pointer w-32"
                                            >
                                                <option value="">— wybierz —</option>
                                                <option value="Wielkanoc">Wielkanoc</option>
                                                <option value="Boże Narodzenie">Boże Narodzenie</option>
                                                <option value="Dzień Dziecka">Dzień Dziecka</option>
                                                <option value="Walentynki">Walentynki</option>
                                                <option value="Halloween">Halloween</option>
                                                <option value="Całoroczne">Całoroczne</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 hover:bg-choco-100 rounded-full text-choco-400 transition-colors flex-shrink-0"
                                >
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Tabs Navigation */}
                    <div className="px-8 flex gap-8 border-t border-choco-50 bg-choco-50/30">
                        {[
                            { id: 'dane_ogolne', label: 'Dane Ogólne' },
                            { id: 'receptura', label: 'Receptura' },
                            { id: 'logistyka', label: 'Logistyka' },
                            { id: 'inne', label: 'Inne' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => handleTabChange(tab.id)}
                                className={`py-4 px-2 text-[10px] font-black uppercase tracking-widest transition-all relative ${activeTab === tab.id
                                    ? 'text-gold-600'
                                    : 'text-choco-400 hover:text-choco-600'
                                    }`}
                            >
                                {tab.label}
                                {activeTab === tab.id && (
                                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-gold-600 rounded-t-full"></div>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content Section (Scrollable) */}
                <div className="flex-1 overflow-auto p-8 custom-scrollbar">
                    <div className="space-y-10 pb-10">
                        {activeTab === 'dane_ogolne' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 space-y-10">
                                {/* Ingredients Section */}
                                <div>
                                    <div className="flex justify-between items-center mb-6">
                                        <h3 className="text-lg font-black text-choco-800 flex items-center gap-2">
                                            <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                            Skład Surowcowy
                                        </h3>
                                        <div className="relative">
                                            <button
                                                onClick={() => setShowAddMenu(!showAddMenu)}
                                                className="flex items-center gap-2 text-sm text-choco-600 font-bold hover:text-choco-800 transition-colors bg-white border border-choco-200 px-4 py-2 rounded-xl shadow-sm"
                                            >
                                                <Plus className="w-4 h-4" />
                                                Dodaj Surowiec
                                            </button>

                                            {showAddMenu && (
                                                <div className="absolute right-0 mt-2 w-64 bg-white border border-choco-100 rounded-2xl shadow-2xl z-20 max-h-64 overflow-auto custom-scrollbar p-2 animate-in fade-in zoom-in duration-200">
                                                    <div className="p-2 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-50 mb-2">Wybierz z bazy</div>
                                                    {availableSurowce.filter(s => !product.skladniki.find(ps => ps.surowiec_id === s.id)).map(s => (
                                                        <button
                                                            key={s.id}
                                                            onClick={() => addSkladnik(s)}
                                                            className="w-full text-left px-4 py-3 hover:bg-choco-50 rounded-xl text-sm font-bold text-choco-800 transition-colors"
                                                        >
                                                            {s.nazwa}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {product.skladniki.map((sk, idx) => (
                                            <div key={idx} className="bg-white border border-choco-100 rounded-2xl p-4 flex items-center justify-between group hover:border-choco-400 transition-all shadow-sm">
                                                <div className="flex-1">
                                                    <p className="font-bold text-choco-800">{sk.surowiec.nazwa}</p>
                                                    <p className="text-[10px] text-choco-500 uppercase font-bold tracking-widest">Kolejność: {sk.kolejnosc}</p>
                                                </div>
                                                <div className="flex items-center gap-6">
                                                    <div className="relative">
                                                        <input
                                                            type="number"
                                                            step="0.1"
                                                            value={sk.procent}
                                                            onChange={(e) => updateSkladnikProcent(idx, e.target.value)}
                                                            className="w-24 bg-choco-50 border border-choco-100 rounded-xl py-2 px-3 text-right text-sm font-bold text-choco-700 focus:outline-none focus:ring-2 focus:ring-choco-200"
                                                        />
                                                        <span className="absolute -right-5 top-1/2 -translate-y-1/2 text-choco-500 text-sm font-bold">%</span>
                                                    </div>
                                                    <button
                                                        onClick={() => removeSkladnik(idx)}
                                                        className="p-2 text-choco-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-6 p-5 rounded-2xl bg-gold-600/5 border border-gold-600/10 flex items-center justify-between">
                                        <span className="text-sm font-bold text-choco-600 uppercase tracking-widest">Suma zawartości:</span>
                                        <span className={`text-xl font-black ${Math.abs(product.skladniki.reduce((acc, s) => acc + s.procent, 0) - 100) < 0.1 ? 'text-green-600' : 'text-gold-600'}`}>
                                            {product.skladniki.reduce((acc, s) => acc + s.procent, 0).toFixed(2)}%
                                        </span>
                                    </div>
                                </div>

                                {/* Nazwa prawna / Opis produktu */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        Nazwa prawna produktu / opis produktu
                                    </h3>
                                    <div className="relative bg-white border border-choco-100 rounded-2xl shadow-sm p-4">
                                        <textarea
                                            value={product.prawna_nazwa_pl || ''}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setProduct({ ...product, prawna_nazwa_pl: val });
                                                if (val.length > 0) fetchSuggestions('prawna_nazwa_pl', val);
                                                else setSuggestions({ ...suggestions, prawna_nazwa_pl: [] });
                                            }}
                                            onFocus={() => {
                                                const val = product.prawna_nazwa_pl || '';
                                                if (val.length > 0) fetchSuggestions('prawna_nazwa_pl', val);
                                            }}
                                            className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 min-h-[100px] resize-y custom-scrollbar"
                                            placeholder="Wpisz nazwę prawną lub opis produktu..."
                                        />
                                        {suggestions['prawna_nazwa_pl'] && suggestions['prawna_nazwa_pl'].length > 0 && (
                                            <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                {suggestions['prawna_nazwa_pl'].map((s, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => {
                                                            setProduct({ ...product, prawna_nazwa_pl: s });
                                                            setSuggestions({ ...suggestions, prawna_nazwa_pl: [] });
                                                        }}
                                                        className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                    >
                                                        {s}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* CN i PKWiU */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6 uppercase tracking-wider">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        CN i PKWiU
                                    </h3>
                                    <div className="border border-choco-100 rounded-2xl bg-white shadow-sm">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-choco-50/50">
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 w-1/3 rounded-tl-2xl">Kod</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 rounded-tr-2xl">Rozwinięcie</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {[
                                                    { key: 'kod_cn', label: 'CN' },
                                                    { key: 'kod_pkwiu', label: 'PKWiU' }
                                                ].map((field) => (
                                                    <tr key={field.key} className="border-b border-choco-50 last:border-0 hover:bg-choco-50/30 transition-colors">
                                                        <td className="px-6 py-4 text-sm font-bold text-choco-700 uppercase tracking-tight">{field.label}</td>
                                                        <td className="px-4 py-2 relative">
                                                            <input
                                                                type="text"
                                                                value={product[field.key] || ''}
                                                                onChange={(e) => {
                                                                    const val = e.target.value;
                                                                    setProduct({ ...product, [field.key]: val });
                                                                    if (val.length > 0) fetchSuggestions(field.key, val);
                                                                    else setSuggestions({ ...suggestions, [field.key]: [] });
                                                                }}
                                                                onFocus={() => {
                                                                    const val = product[field.key] || '';
                                                                    if (val.length > 0) fetchSuggestions(field.key, val);
                                                                }}
                                                                className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2"
                                                                placeholder={`Wpisz kod ${field.label}...`}
                                                            />
                                                            {suggestions[field.key] && suggestions[field.key].length > 0 && (
                                                                <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                                    {suggestions[field.key].map((s, i) => (
                                                                        <button
                                                                            key={i}
                                                                            onClick={() => {
                                                                                setProduct({ ...product, [field.key]: s });
                                                                                setSuggestions({ ...suggestions, [field.key]: [] });
                                                                            }}
                                                                            className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                                        >
                                                                            {s}
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Certyfikaty */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        Certyfikaty
                                    </h3>
                                    <div className="border border-choco-100 rounded-2xl bg-white shadow-sm">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-choco-50/50">
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 rounded-tl-2xl">Rodzaj</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">COID</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 rounded-tr-2xl">Data ważności certyfikatu</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {(() => {
                                                    const certs = Array.isArray(product.certyfikaty) ? product.certyfikaty : (typeof product.certyfikaty === 'string' ? JSON.parse(product.certyfikaty || '[]') : []);
                                                    // Ensure there is at least one object
                                                    const cert = certs[0] || { rodzaj: '', coid: '', data_waznosci: '' };
                                                    return (
                                                        <tr className="hover:bg-choco-50/30 transition-colors">
                                                            <td className="px-4 py-2 relative">
                                                                <input
                                                                    type="text"
                                                                    value={cert.rodzaj}
                                                                    onChange={(e) => {
                                                                        const val = e.target.value;
                                                                        const updatedCert = { ...cert, rodzaj: val };
                                                                        setProduct({ ...product, certyfikaty: [updatedCert] });
                                                                        if (val.length > 0) fetchSuggestions('certyfikat_rodzaj', val);
                                                                        else setSuggestions({ ...suggestions, certyfikat_rodzaj: [] });
                                                                    }}
                                                                    onFocus={() => {
                                                                        if (cert.rodzaj.length > 0) fetchSuggestions('certyfikat_rodzaj', cert.rodzaj);
                                                                    }}
                                                                    className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2"
                                                                    placeholder="Np. IFS Food 8.0"
                                                                />
                                                                {suggestions['certyfikat_rodzaj'] && suggestions['certyfikat_rodzaj'].length > 0 && (
                                                                    <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-30 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                                        {suggestions['certyfikat_rodzaj'].map((s, i) => (
                                                                            <button
                                                                                key={i}
                                                                                onClick={() => {
                                                                                    const updatedCert = { ...cert, rodzaj: s };
                                                                                    setProduct({ ...product, certyfikaty: [updatedCert] });
                                                                                    setSuggestions({ ...suggestions, certyfikat_rodzaj: [] });
                                                                                }}
                                                                                className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                                            >
                                                                                {s}
                                                                            </button>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </td>
                                                            <td className="px-4 py-2">
                                                                <input
                                                                    type="text"
                                                                    value={cert.coid}
                                                                    onChange={(e) => {
                                                                        const updatedCert = { ...cert, coid: e.target.value };
                                                                        setProduct({ ...product, certyfikaty: [updatedCert] });
                                                                    }}
                                                                    className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2"
                                                                    placeholder="Wpisz COID"
                                                                />
                                                            </td>
                                                            <td className="px-4 py-2">
                                                                <input
                                                                    type="date"
                                                                    value={cert.data_waznosci}
                                                                    onChange={(e) => {
                                                                        const updatedCert = { ...cert, data_waznosci: e.target.value };
                                                                        setProduct({ ...product, certyfikaty: [updatedCert] });
                                                                    }}
                                                                    className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2"
                                                                />
                                                            </td>
                                                        </tr>
                                                    )
                                                })()}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'receptura' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 space-y-10">
                                {/* Generated Data Section */}
                                <div className="grid grid-cols-2 gap-8 pt-4">
                                    <div>
                                        <h4 className="text-[10px] font-black text-choco-600 uppercase tracking-widest mb-4">Wartości odżywcze / 100g</h4>
                                        <div className="space-y-1">
                                            {liveNutrition && Object.entries(liveNutrition).map(([key, val]) => (
                                                <div key={key} className="flex justify-between text-sm py-2 border-b border-choco-100/50 last:border-0 text-choco-600">
                                                    <span>{nutritionLabels[key]}</span>
                                                    <span className="text-choco-900 font-bold">{key === 'sol' ? val.toFixed(2) : key === 'bialko' ? val.toFixed(1) : Math.round(val)} {key.includes('energia') ? (key === 'energia_kj' ? 'kJ' : 'kcal') : 'g'}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <h4 className="text-[10px] font-black text-choco-600 uppercase tracking-widest mb-4">Alergeny</h4>
                                        <div className="flex flex-wrap gap-2">
                                            {analysis && Object.entries(analysis.allergens).map(([alg, status]) => (
                                                <span key={alg} className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-tight ${status === "Zawiera" ? 'bg-red-50 text-red-600 border border-red-200' :
                                                    status === "Może zawierać" ? 'bg-gold-600/10 text-gold-600 border border-gold-600/20' :
                                                        'bg-choco-50 text-choco-400 border border-choco-100'
                                                    }`}>
                                                    {alg.replace('_', ' ').replace('dwutlenek siarki', 'SIARKCZYNY')}: {status}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>


                                {/* Ingr List */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h4 className="text-[10px] font-black text-choco-600 uppercase tracking-widest mb-4">Skład</h4>
                                    <div
                                        className="p-6 bg-white rounded-2xl border border-choco-100 text-sm text-choco-700 leading-relaxed shadow-inner italic"
                                        dangerouslySetInnerHTML={{ __html: boldAllergens(analysis?.ingredients_pl || '') }}
                                    />
                                </div>

                                {/* Percentage and Origins List */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h4 className="text-[10px] font-black text-choco-600 uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <Info className="w-3 h-3 text-gold-600" />
                                        Procentowy udział składników w produkcji i ich kraje pochodzenia
                                    </h4>
                                    <div className="space-y-1">
                                        {analysis?.ingredient_origins?.map((item, idx) => (
                                            <div key={idx} className="flex items-center gap-3 py-2.5 px-4 bg-white border border-choco-50 rounded-xl hover:border-gold-200 transition-colors group">
                                                <span className="font-bold text-choco-800 group-hover:text-choco-950 transition-colors">
                                                    {item.name}
                                                </span>
                                                <span className="text-choco-300">—</span>
                                                <span className="font-black text-gold-600 w-20 text-center">
                                                    {(item.percent >= 1 ? item.percent.toFixed(1) : item.percent.toFixed(2)).replace('.', ',')}%
                                                </span>
                                                <span className="text-choco-300">—</span>
                                                <span className="text-choco-500 italic font-medium flex-1">
                                                    {item.countries.join(', ') || 'brak danych'}
                                                </span>
                                            </div>
                                        ))}
                                        {(!analysis?.ingredient_origins || analysis.ingredient_origins.length === 0) && (
                                            <div className="text-center py-8 text-choco-300 text-[10px] font-bold uppercase tracking-widest border-2 border-dashed border-choco-50 rounded-2xl">
                                                Brak danych do wygenerowania zestawienia
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'logistyka' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 space-y-10">
                                {/* SEKCJA: WYMIARY */}
                                <div className="pt-4">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        1. WYMIARY
                                    </h3>
                                    <div className="overflow-hidden border border-choco-100 rounded-2xl bg-white shadow-sm">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-choco-50/50">
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">Poziom</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">Wysokość [cm]</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">Szerokość [cm]</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">Głębokość [cm]</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {[
                                                    { label: 'Produkt solo', prefix: 'logistyka_wymiary_solo' },
                                                    { label: 'W opakowaniu jednostkowym', prefix: 'logistyka_wymiary_jednostka' },
                                                    { label: 'Opakowanie zbiorcze 1°', prefix: 'logistyka_wymiary_zbiorcze1', affectsPalletHeight: true },
                                                    { label: 'Opakowanie zbiorcze 2°', prefix: 'logistyka_wymiary_zbiorcze2', affectsPalletHeight: true },
                                                    { label: 'Opakowanie zbiorcze 3°', prefix: 'logistyka_wymiary_zbiorcze3', affectsPalletHeight: true },
                                                ].map((row) => (
                                                    <tr key={row.prefix} className="border-b border-choco-50 last:border-0 hover:bg-choco-50/30 transition-colors">
                                                        <td className="px-6 py-4 text-sm font-bold text-choco-700">{row.label}</td>
                                                        {['h', 'w', 'd'].map((dim) => (
                                                            <td key={dim} className="px-4 py-2">
                                                                <input
                                                                    type="number"
                                                                    step="0.01"
                                                                    min="0"
                                                                    value={product[`${row.prefix}_${dim}`] || 0}
                                                                    onChange={(e) => {
                                                                if (dim === 'h' && row.affectsPalletHeight) palletHeightChangedRef.current = true
                                                                setProduct({ ...product, [`${row.prefix}_${dim}`]: parseFloat(e.target.value) || 0 })
                                                            }}
                                                                    className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 text-center font-medium"
                                                                />
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                    <div className="mt-6 flex items-center gap-4 bg-white border border-choco-100 p-4 rounded-2xl shadow-sm">
                                        <label className="text-sm font-bold text-choco-600 uppercase tracking-widest min-w-[120px]">Rodzaj palety:</label>
                                        <div className="relative flex-1">
                                            <input
                                                type="text"
                                                value={product.logistyka_rodzaj_palety || ''}
                                                onChange={(e) => {
                                                    const val = e.target.value;
                                                    setProduct({ ...product, logistyka_rodzaj_palety: val });
                                                    if (val.length > 0) fetchSuggestions('logistyka_rodzaj_palety', val);
                                                    else setSuggestions({ ...suggestions, logistyka_rodzaj_palety: [] });
                                                }}
                                                onFocus={() => {
                                                    const val = product.logistyka_rodzaj_palety || '';
                                                    if (val.length > 0) fetchSuggestions('logistyka_rodzaj_palety', val);
                                                }}
                                                placeholder="Np. LPR/EUR 800 x 1200 mm"
                                                className="w-full bg-choco-50/50 border-0 focus:ring-2 focus:ring-choco-100 rounded-xl px-4 py-2 text-sm text-choco-800 font-medium"
                                            />
                                            {suggestions['logistyka_rodzaj_palety'] && suggestions['logistyka_rodzaj_palety'].length > 0 && (
                                                <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto p-1">
                                                    {suggestions['logistyka_rodzaj_palety'].map((s, i) => (
                                                        <button
                                                            key={i}
                                                            onClick={() => {
                                                                setProduct({ ...product, logistyka_rodzaj_palety: s });
                                                                setSuggestions({ ...suggestions, logistyka_rodzaj_palety: [] });
                                                            }}
                                                            className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600"
                                                        >
                                                            {s}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* SEKCJA: WAGI */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        2. WAGI
                                    </h3>
                                    <div className="overflow-hidden border border-choco-100 rounded-2xl bg-white shadow-sm max-w-2xl">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-choco-50/50">
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100">Parametr</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 text-center">Wartość [kg]</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {[
                                                    { label: 'Waga netto sztuki', key: 'logistyka_waga_netto_szt' },
                                                    { label: 'Waga brutto sztuki', key: 'logistyka_waga_brutto_szt' },
                                                    { label: 'Waga netto opakowania zbiorczego', key: 'logistyka_waga_netto_zbiorcze' },
                                                    { label: 'Waga brutto opakowania zbiorczego', key: 'logistyka_waga_brutto_zbiorcze' },
                                                    { label: 'Waga netto palety', key: 'logistyka_waga_netto_paleta' },
                                                    { label: 'Waga brutto palety', key: 'logistyka_waga_brutto_paleta' },
                                                ].map((row) => (
                                                    <tr key={row.key} className="border-b border-choco-50 last:border-0 hover:bg-choco-50/30 transition-colors">
                                                        <td className="px-6 py-4 text-sm font-bold text-choco-700">{row.label}</td>
                                                        <td className="px-4 py-2">
                                                            <input
                                                                type="number"
                                                                step="0.001"
                                                                min="0"
                                                                value={product[row.key] || 0}
                                                                onChange={(e) => setProduct({ ...product, [row.key]: parseFloat(e.target.value) || 0 })}
                                                                className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 text-center font-bold"
                                                            />
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* SEKCJA: PALETYZACJA */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        3. PALETYZACJA
                                    </h3>
                                    <div className="grid grid-cols-2 gap-x-12 gap-y-6 bg-white border border-choco-100 p-8 rounded-2xl shadow-sm">
                                        {[
                                            { label: 'Ilość sztuk w opakowaniu zbiorczym [szt]', key: 'logistyka_sztuk_w_zbiorczym', isCalcInput: true },
                                            { label: 'Ilość kartonów na warstwie [szt]', key: 'logistyka_kartonow_na_warstwie', isCalcInput: true },
                                            { label: 'Ilość warstw na palecie [szt]', key: 'logistyka_warstw_na_palecie', isCalcInput: true, isPalletHeightInput: true },
                                            { label: 'Ilość sztuk na warstwie palety [szt]', key: 'logistyka_sztuk_na_warstwie', isAuto: true },
                                            { label: 'Ilość kartonów na palecie [szt]', key: 'logistyka_kartonow_na_palecie', isAuto: true },
                                            { label: 'Ilość sztuk na palecie [szt]', key: 'logistyka_sztuk_na_palecie', isAuto: true },
                                            { label: 'Wysokość palety z nośnikiem [cm]', key: 'logistyka_wysokosc_palety', isFloat: true, isAuto: true },
                                        ].map((field) => (
                                            <div key={field.key} className="flex flex-col gap-2">
                                                <label className="text-[10px] font-black text-choco-400 uppercase tracking-widest flex items-center gap-2">
                                                    {field.label}
                                                    {field.isAuto && <span className="text-gold-600 text-[8px] bg-gold-600/10 px-1.5 py-0.5 rounded-full font-black normal-case">auto</span>}
                                                </label>
                                                <input
                                                    type="number"
                                                    step={field.isFloat ? "0.01" : "1"}
                                                    min="0"
                                                    value={product[field.key] ?? ''}
                                                    onChange={(e) => {
                                                        if (field.isCalcInput) userChangedInputRef.current = true
                                                        if (field.isPalletHeightInput) palletHeightChangedRef.current = true
                                                        const raw = e.target.value
                                                        const val = raw === '' ? null : (field.isFloat ? parseFloat(raw) : parseInt(raw, 10))
                                                        setProduct({ ...product, [field.key]: (val !== null && isNaN(val)) ? null : val })
                                                    }}
                                                    className="w-full bg-choco-50/30 border border-choco-100 rounded-xl px-4 py-3 text-sm font-bold text-choco-800 focus:outline-none focus:ring-2 focus:ring-choco-100 transition-all"
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeTab === 'inne' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-300 space-y-10">
                                {/* Organoleptyka Section */}
                                <div className="pt-4">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        Organoleptyka
                                    </h3>
                                    <div className="border border-choco-100 rounded-2xl bg-white shadow-sm">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-choco-50/50">
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 w-1/3 rounded-tl-2xl">Parametr</th>
                                                    <th className="px-6 py-4 text-[10px] font-black text-choco-400 uppercase tracking-widest border-b border-choco-100 rounded-tr-2xl">Opis</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {[
                                                    { key: 'organoleptyka_smak', label: 'SMAK' },
                                                    { key: 'organoleptyka_zapach', label: 'ZAPACH' },
                                                    { key: 'organoleptyka_kolor', label: 'KOLOR' },
                                                    { key: 'organoleptyka_wyglad_zewnetrzny', label: 'WYGLĄD ZEWNĘTRZNY' },
                                                    { key: 'organoleptyka_wyglad_na_przekroju', label: 'WYGLĄD NA PRZEKROJU' }
                                                ].map((field) => (
                                                    <tr key={field.key} className="border-b border-choco-50 last:border-0 group hover:bg-choco-50/30 transition-colors">
                                                        <td className="px-6 py-4 text-sm font-bold text-choco-700 align-top uppercase tracking-tight">
                                                            {field.label}
                                                        </td>
                                                        <td className="px-4 py-2 relative">
                                                            <textarea
                                                                value={product[field.key] || ''}
                                                                onChange={(e) => {
                                                                    const val = e.target.value;
                                                                    setProduct({ ...product, [field.key]: val });
                                                                    if (val.length > 0) {
                                                                        fetchSuggestions(field.key, val);
                                                                    } else {
                                                                        setSuggestions({ ...suggestions, [field.key]: [] });
                                                                    }
                                                                }}
                                                                onFocus={() => {
                                                                    const val = product[field.key] || '';
                                                                    if (val.length > 0) fetchSuggestions(field.key, val);
                                                                }}
                                                                onDoubleClick={() => {
                                                                    const val = product[field.key] || '';
                                                                    fetchSuggestions(field.key, val, true);
                                                                }}
                                                                className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 min-h-[60px] resize-y custom-scrollbar"
                                                                placeholder={`Wpisz opis dla: ${field.label.toLowerCase()}...`}
                                                            />
                                                            {suggestions[field.key] && suggestions[field.key].length > 0 && (
                                                                <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                                    {suggestions[field.key].map((s, i) => (
                                                                        <button
                                                                            key={i}
                                                                            onClick={() => {
                                                                                setProduct({ ...product, [field.key]: s });
                                                                                setSuggestions({ ...suggestions, [field.key]: [] });
                                                                            }}
                                                                            className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                                        >
                                                                            {s}
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6 uppercase tracking-wider">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        WARUNKI PRZECHOWYWANIA I TRANSPORTU
                                    </h3>
                                    <div className="relative bg-white border border-choco-100 rounded-2xl shadow-sm p-4">
                                        <textarea
                                            value={product.warunki_przechowywania || ''}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setProduct({ ...product, warunki_przechowywania: val });
                                                if (val.length > 0) fetchSuggestions('warunki_przechowywania', val);
                                                else setSuggestions({ ...suggestions, warunki_przechowywania: [] });
                                            }}
                                            onFocus={() => {
                                                const val = product.warunki_przechowywania || '';
                                                if (val.length > 0) fetchSuggestions('warunki_przechowywania', val);
                                            }}
                                            onDoubleClick={() => {
                                                const val = product.warunki_przechowywania || '';
                                                fetchSuggestions('warunki_przechowywania', val, true);
                                            }}
                                            className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 min-h-[80px] resize-y custom-scrollbar"
                                            placeholder="Wpisz warunki przechowywania..."
                                        />
                                        {suggestions['warunki_przechowywania'] && suggestions['warunki_przechowywania'].length > 0 && (
                                            <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                {suggestions['warunki_przechowywania'].map((s, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => {
                                                            setProduct({ ...product, warunki_przechowywania: s });
                                                            setSuggestions({ ...suggestions, warunki_przechowywania: [] });
                                                        }}
                                                        className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                    >
                                                        {s}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* TERMIN PRZYDATNOŚCI DO SPOŻYCIA */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6 uppercase tracking-wider">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        TERMIN PRZYDATNOŚCI DO SPOŻYCIA
                                    </h3>
                                    <div className="relative bg-white border border-choco-100 rounded-2xl shadow-sm p-4">
                                        <textarea
                                            value={product.termin_przydatnosci || ''}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setProduct({ ...product, termin_przydatnosci: val });
                                                if (val.length > 0) fetchSuggestions('termin_przydatnosci', val);
                                                else setSuggestions({ ...suggestions, termin_przydatnosci: [] });
                                            }}
                                            onFocus={() => {
                                                const val = product.termin_przydatnosci || '';
                                                if (val.length > 0) fetchSuggestions('termin_przydatnosci', val);
                                            }}
                                            onDoubleClick={() => {
                                                const val = product.termin_przydatnosci || '';
                                                fetchSuggestions('termin_przydatnosci', val, true);
                                            }}
                                            className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 min-h-[60px] resize-y custom-scrollbar"
                                            placeholder="Np. 12 miesięcy od daty produkcji..."
                                        />
                                        {suggestions['termin_przydatnosci'] && suggestions['termin_przydatnosci'].length > 0 && (
                                            <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                {suggestions['termin_przydatnosci'].map((s, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => {
                                                            setProduct({ ...product, termin_przydatnosci: s });
                                                            setSuggestions({ ...suggestions, termin_przydatnosci: [] });
                                                        }}
                                                        className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                    >
                                                        {s}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* WYRAŻENIE I FORMAT */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6 uppercase tracking-wider">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        WYRAŻENIE I FORMAT
                                    </h3>
                                    <div className="relative bg-white border border-choco-100 rounded-2xl shadow-sm p-4">
                                        <textarea
                                            value={product.wyrazenie_format_daty || ''}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setProduct({ ...product, wyrazenie_format_daty: val });
                                                if (val.length > 0) fetchSuggestions('wyrazenie_format_daty', val);
                                                else setSuggestions({ ...suggestions, wyrazenie_format_daty: [] });
                                            }}
                                            onFocus={() => {
                                                const val = product.wyrazenie_format_daty || '';
                                                if (val.length > 0) fetchSuggestions('wyrazenie_format_daty', val);
                                            }}
                                            onDoubleClick={() => {
                                                const val = product.wyrazenie_format_daty || '';
                                                fetchSuggestions('wyrazenie_format_daty', val, true);
                                            }}
                                            className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 min-h-[60px] resize-y custom-scrollbar"
                                            placeholder="Np. Najlepiej spożyć przed końcem: MM.RRRR..."
                                        />
                                        {suggestions['wyrazenie_format_daty'] && suggestions['wyrazenie_format_daty'].length > 0 && (
                                            <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                {suggestions['wyrazenie_format_daty'].map((s, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => {
                                                            setProduct({ ...product, wyrazenie_format_daty: s });
                                                            setSuggestions({ ...suggestions, wyrazenie_format_daty: [] });
                                                        }}
                                                        className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                    >
                                                        {s}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* INFORMACJE DODATKOWE */}
                                <div className="pt-8 border-t border-choco-100">
                                    <h3 className="text-lg font-black text-choco-800 flex items-center gap-2 mb-6 uppercase tracking-wider">
                                        <div className="w-1.5 h-6 bg-gold-600 rounded-full"></div>
                                        INFORMACJE DODATKOWE
                                    </h3>
                                    <div className="relative bg-white border border-choco-100 rounded-2xl shadow-sm p-4">
                                        <textarea
                                            value={product.informacje_dodatkowe || ''}
                                            onChange={(e) => {
                                                const val = e.target.value;
                                                setProduct({ ...product, informacje_dodatkowe: val });
                                                if (val.length > 0) fetchSuggestions('informacje_dodatkowe', val);
                                                else setSuggestions({ ...suggestions, informacje_dodatkowe: [] });
                                            }}
                                            onFocus={() => {
                                                const val = product.informacje_dodatkowe || '';
                                                if (val.length > 0) fetchSuggestions('informacje_dodatkowe', val);
                                            }}
                                            onDoubleClick={() => {
                                                const val = product.informacje_dodatkowe || '';
                                                fetchSuggestions('informacje_dodatkowe', val, true);
                                            }}
                                            className="w-full bg-transparent border-0 focus:ring-0 text-sm text-choco-800 p-2 min-h-[100px] resize-y custom-scrollbar"
                                            placeholder="Np. Produkt gotowy do spożycia po rozmrożeniu..."
                                        />
                                        {suggestions['informacje_dodatkowe'] && suggestions['informacje_dodatkowe'].length > 0 && (
                                            <div className="absolute left-4 right-4 top-full -mt-1 bg-white border border-choco-100 rounded-xl shadow-xl z-20 max-h-48 overflow-auto custom-scrollbar p-1 animate-in fade-in slide-in-from-top-2 duration-200">
                                                {suggestions['informacje_dodatkowe'].map((s, i) => (
                                                    <button
                                                        key={i}
                                                        onClick={() => {
                                                            setProduct({ ...product, informacje_dodatkowe: s });
                                                            setSuggestions({ ...suggestions, informacje_dodatkowe: [] });
                                                        }}
                                                        className="w-full text-left px-3 py-2 hover:bg-choco-50 rounded-lg text-xs font-medium text-choco-600 transition-colors border-b border-choco-50 last:border-0"
                                                    >
                                                        {s}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div >

                {/* Footer */}
                <div className="px-6 py-4 border-t border-choco-100 flex items-center gap-2 bg-white/80 backdrop-blur-xl flex-wrap">
                    {/* Export buttons — secondary, compact */}
                    <button
                        onClick={() => handleDownload('pl')}
                        className="flex items-center gap-1.5 bg-choco-50 hover:bg-choco-100 text-choco-600 border border-choco-200 px-3 py-2 rounded-lg font-bold transition-all text-[10px] uppercase tracking-widest whitespace-nowrap"
                    >
                        <FileDown className="w-3.5 h-3.5 shrink-0" />
                        Eksport PL
                    </button>
                    <button
                        onClick={handleDownloadExcelEn}
                        className="flex items-center gap-1.5 bg-choco-50 hover:bg-choco-100 text-choco-600 border border-choco-200 px-3 py-2 rounded-lg font-bold transition-all text-[10px] uppercase tracking-widest whitespace-nowrap"
                    >
                        <FileDown className="w-3.5 h-3.5 shrink-0" />
                        Eksport EN
                    </button>
                    <button
                        onClick={handleDownloadPDF}
                        className="flex items-center gap-1.5 bg-gold-50 hover:bg-gold-100 text-gold-700 border border-gold-200 px-3 py-2 rounded-lg font-bold transition-all text-[10px] uppercase tracking-widest whitespace-nowrap"
                    >
                        <FileDown className="w-3.5 h-3.5 shrink-0" />
                        Eksport PL PDF
                    </button>
                    <button
                        onClick={handleDownloadPDFEn}
                        className="flex items-center gap-1.5 bg-gold-50 hover:bg-gold-100 text-gold-700 border border-gold-200 px-3 py-2 rounded-lg font-bold transition-all text-[10px] uppercase tracking-widest whitespace-nowrap"
                    >
                        <FileDown className="w-3.5 h-3.5 shrink-0" />
                        Eksport EN PDF
                    </button>

                    {/* Spacer */}
                    <div className="flex-1" />

                    {/* Primary save button */}
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 bg-choco-800 hover:bg-choco-700 text-white px-6 py-2.5 rounded-xl font-black transition-all shadow-xl shadow-choco-900/30 disabled:opacity-50 text-xs uppercase tracking-widest whitespace-nowrap shrink-0"
                    >
                        {saving ? 'Czekaj...' : <><Save className="w-4 h-4" /> Zapisz dane</>}
                    </button>
                </div>
            </div >
        </div >
    )
}
