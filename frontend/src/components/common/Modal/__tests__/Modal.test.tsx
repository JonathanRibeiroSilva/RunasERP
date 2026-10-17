/**
 * Dois defeitos que só aparecem num navegador de verdade, e que o jsdom não
 * enxerga: o overlay preso debaixo da Navbar, e o Bootstrap pisando em
 * `.modal-dialog` (pointer-events: none herdado por todo campo — a roda do mouse
 * rolava a página de trás, e um clique dentro do card fechava o modal). Estes
 * testes guardam as duas causas, não o sintoma.
 */

import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import Modal from '../Modal';
import scss from '../Modal.scss?raw';

describe('Modal', () => {
  it('renderiza em document.body, fora do contexto de empilhamento de quem o chamou', () => {
    const { container } = render(
      <div data-testid="host">
        <Modal isOpen title="Provisionar tenant" onClose={() => {}}>
          conteúdo
        </Modal>
      </div>,
    );

    const dialog = screen.getByRole('dialog');
    expect(container.contains(dialog)).toBe(false);
    expect(dialog.closest('.modal-overlay')?.parentElement).toBe(document.body);
  });

  it('fecha pelo overlay e pelo ESC, mas não por clique dentro do card', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen title="T" onClose={onClose}>
        conteúdo
      </Modal>,
    );

    fireEvent.click(screen.getByRole('dialog'));
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('presentation'));
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('não renderiza nada fechado', () => {
    render(
      <Modal isOpen={false} title="T" onClose={() => {}}>
        conteúdo
      </Modal>,
    );
    expect(screen.queryByRole('dialog')).toBeNull();
  });
});

describe('Modal.scss', () => {
  it('não usa `.modal-dialog` solto: o Bootstrap, carregado depois, vence o empate', () => {
    expect(scss).not.toMatch(/^\.modal-dialog\s*\{/m);
  });

  it('reafirma o que o Bootstrap pisa, com um seletor a mais', () => {
    const bloco = scss.match(/\.modal-overlay\s+\.modal-dialog\s*\{([^}]*)\}/)?.[1] ?? '';
    expect(bloco).toMatch(/pointer-events:\s*auto/);
    expect(bloco).toMatch(/max-width:\s*520px/);
    expect(bloco).toMatch(/width:\s*100%/);
  });
});
