# TODO: Implementar Stepper no Checkout

## Problema Atual

O **stepper** (navegação por etapas) estava causando problemas de rolagem na página de checkout:
- Ocupava muito espaço vertical
- Conflitava com o scroll da página
- Layout ficava confuso em telas menores

## Solução Temporária

- Stepper foi comentado no código
- Navegação por etapas continua funcionando nos bastidores
- Apenas não está visível para o usuário

## Implementações Futuras

### Opção 1: Stepper Compacto Fixo no Topo

```tsx
// Stepper compacto no header
<div className="checkout-header">
  <button onClick={voltar}>Voltar</button>
  <div className="mini-stepper">
    <span className={step >= 1 ? 'active' : ''}>1</span>
    <span className={step >= 2 ? 'active' : ''}>2</span>
    <span className={step >= 3 ? 'active' : ''}>3</span>
  </div>
  <h1>Finalizar Compra</h1>
</div>
```

**Prós:**
- Sempre visível
- Ocupa pouco espaço
- Simples de implementar

**Contras:**
- Menos informativo
- Pode ser confuso sem labels

### Opção 2: Stepper no Título da Seção

```tsx
// Indicador no título de cada seção
<h2>
  <span className="step-badge">1/3</span>
  Seus dados
</h2>
```

**Prós:**
- Contextual
- Não adiciona elementos extras
- Intuitivo

**Contras:**
- Não mostra progresso total
- Menos visual

### Opção 3: Progress Bar Linear

```tsx
// Barra de progresso simples
<div className="progress-bar">
  <div className="progress-fill" style={{ width: `${(step / 3) * 100}%` }} />
</div>
<p className="progress-label">Etapa {step} de 3</p>
```

**Prós:**
- Minimalista
- Ocupa pouco espaço
- Moderno

**Contras:**
- Não mostra nome das etapas
- Menos interativo

### Opção 4: Stepper em Modal/Drawer (Recomendado para Mobile)

```tsx
// Botão que abre modal com overview
<button onClick={() => setShowProgress(true)}>
  Ver progresso (Etapa {step}/3)
</button>

// Modal com stepper completo
<Modal open={showProgress}>
  <StepperCompleto currentStep={step} />
</Modal>
```

**Prós:**
- Não interfere no layout principal
- Pode ser detalhado
- Ótimo para mobile

**Contras:**
- Requer interação extra
- Mais complexo

### Opção 5: Breadcrumb Horizontal

```tsx
// Breadcrumb tradicional
<div className="breadcrumb">
  <span className={step >= 1 ? 'active' : ''}>Dados</span>
  <span className="separator">›</span>
  <span className={step >= 2 ? 'active' : ''}>Entrega</span>
  <span className="separator">›</span>
  <span className={step >= 3 ? 'active' : ''}>Pagamento</span>
</div>
```

**Prós:**
- Familiar para usuários
- Compacto
- Informativo

**Contras:**
- Pode ficar apertado no mobile
- Menos visual que stepper tradicional

## Recomendação de Implementação

### Desktop
- **Progress Bar Linear** no header + labels das etapas nos títulos das seções
- Limpo, moderno, não interfere no scroll

### Mobile
- **Breadcrumb compacto** ou **indicador de etapa no título**
- Exemplo: "1/3 - Seus dados"

## Código de Referência

O código do stepper original está comentado em:
- `frontend/src/pages/CatalogoPublico/CheckoutPage.tsx` (linhas ~291-305)
- `frontend/src/pages/CatalogoPublico/CheckoutPage.scss` (linhas ~60-130)

## Nomenclatura Correta

- **Stepper**: Componente de navegação por etapas
- **Progress Indicator**: Indicador de progresso
- **Wizard Navigation**: Navegação de assistente/wizard
- **Step Indicator**: Indicador de etapas
- **Breadcrumb**: Migalhas de pão (navegação hierárquica)

No contexto de checkout, o mais comum é:
- **Checkout Stepper**
- **Multi-step Form**
- **Progress Steps**

## Referências de Design

- [Material UI Stepper](https://mui.com/material-ui/react-stepper/)
- [Ant Design Steps](https://ant.design/components/steps)
- [Chakra UI Steps](https://chakra-ui.com/docs/components/stepper)

## Próximos Passos

1. Testar usabilidade sem o stepper
2. Coletar feedback de usuários
3. Decidir qual opção implementar
4. Implementar versão escolhida
5. Testar em diferentes dispositivos
