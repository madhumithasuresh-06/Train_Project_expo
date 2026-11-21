import { useState, useRef, useEffect } from "react";

export default function Autocomplete({ label, placeholder, options, value, onChange, renderOption, getOptionLabel }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const selected = options.find((o) => getOptionLabel(o) === value || o.station_code === value || o.train_number === value);
    if (selected) setQuery(renderOption ? renderOption(selected) : getOptionLabel(selected));
  }, [value, options]);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = options.filter((o) => {
    const text = (renderOption ? renderOption(o) : getOptionLabel(o)).toLowerCase();
    return text.includes(query.toLowerCase());
  });

  return (
    <div ref={ref} className="relative">
      <label className="block text-xs font-medium text-rail-300 mb-1.5 uppercase tracking-wider">{label}</label>
      <input
        type="text"
        value={query}
        placeholder={placeholder}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); onChange(""); }}
        onFocus={() => setOpen(true)}
        className="w-full rounded-xl bg-navy-900/80 border border-rail-700/40 px-4 py-3 text-white placeholder:text-rail-600 focus:outline-none focus:ring-2 focus:ring-rail-500/50 focus:border-rail-500 transition"
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-20 mt-1 w-full max-h-48 overflow-auto rounded-xl bg-navy-900 border border-rail-700/50 shadow-xl shadow-black/40">
          {filtered.map((o, i) => (
            <li key={i}>
              <button
                type="button"
                className="w-full text-left px-4 py-2.5 text-sm hover:bg-rail-800/40 transition"
                onClick={() => {
                  const label = renderOption ? renderOption(o) : getOptionLabel(o);
                  setQuery(label);
                  onChange(o.station_code || o.train_number);
                  setOpen(false);
                }}
              >
                {renderOption ? renderOption(o) : getOptionLabel(o)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
