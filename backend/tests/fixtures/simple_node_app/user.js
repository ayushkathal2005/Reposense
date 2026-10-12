import { logInfo } from './logger.js';

class BaseEntity {
  constructor(id) {
    this.id = id;
  }
}

/**
 * Represents a user account in the system.
 */
class User extends BaseEntity {
  constructor(id, name) {
    super(id);
    this.name = name;
  }

  save() {
    logInfo("Saving user: " + this.name);
  }
}

export function createUser(id, name) {
  const u = new User(id, name);
  u.save();
  return u;
}
