# Marketing Campaign Multi-Agent System

Un sistema autonomo di agenti AI per la gestione completa di campagne di marketing, costruito con LangGraph e il pattern Deep Agents.

## 🎯 Obiettivo del Progetto

Questo sistema implementa un'architettura multi-agente che simula un team di marketing completo, in grado di:
- Pianificare strategie di marketing basate su ricerche di mercato
- Creare contenuti per social media (testo e visual)
- Analizzare performance simulate
- Iterare e migliorare basandosi sui risultati

## 🏗️ Architettura

### Agenti Principali

#### 1. **Project Manager Agent** (Deep Agent)
Il coordinatore principale che:
- Riceve il brief della campagna
- Crea e gestisce TODO list
- Delega task agli agenti specializzati
- Gestisce il ciclo iterativo (fino a 3 iterazioni)
- Mantiene un filesystem virtuale per il context offloading

#### 2. **Strategy Planner Agent** (Sub-agent)
Specializzato in ricerca e strategia:
- Ricerca insights sul target audience
- Analizza competitor e trend di mercato
- Sviluppa strategie di marketing complete
- Adatta la strategia basandosi sul feedback

#### 3. **Content Creator Agent** (Sub-agent)
Crea contenuti social media:
- Genera caption per post LinkedIn
- Crea descrizioni dettagliate per visual
- Allinea i contenuti alla strategia
- Ottimizza per engagement

#### 4. **Analytics Agent** (Sub-agent)
Simula e analizza performance:
- Genera metriche realistiche (reach, engagement, conversions)
- Assegna performance score (0-100)
- Fornisce feedback actionable
- Traccia progressi tra iterazioni

### Workflow della Campagna

```
1. Campaign Brief Input
        ↓
2. Strategy Planning (ricerca + pianificazione)
        ↓
3. Content Creation (caption + visual)
        ↓
4. Analytics & Simulation (metriche + feedback)
        ↓
5. Iteration Decision
        ├→ Score >= Threshold: Successo → Next iteration o Complete
        └→ Score < Threshold: Feedback → Back to Strategy (up to max_iterations)
```
