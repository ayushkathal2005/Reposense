import { Currency } from './types';

export interface PaymentConfig {
  apiKey: string;
  currency: Currency;
}

export type TransactionStatus = 'pending' | 'success' | 'failed';

/**
 * Handles payment transactions with validation.
 */
export class PaymentService {
  constructor(private config: PaymentConfig) {}

  public processPayment(amount: number): TransactionStatus {
    this.validate(amount);
    return 'success';
  }

  private validate(amount: number): boolean {
    return amount > 0;
  }
}

export const executeOrder = (service: PaymentService, amount: number) => {
  return service.processPayment(amount);
};
