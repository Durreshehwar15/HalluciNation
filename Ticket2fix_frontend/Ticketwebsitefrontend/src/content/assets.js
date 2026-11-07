// All image paths live here. Put the files in  public/images/  with these exact names
// (or change the names below).
export const IMG = {
  logo: '/images/logo.png',                    // your logo, shown in the middle of the top bar
  logo1: '/images/logo1.png',                  // top navigation bar
  logo2: '/images/logo2.png',
  main: '/images/mainimage.png',               // first picture visitors see
  board: '/images/gameboardpage.png',          // empty town square used for the game board
  charge: '/images/You stay in charge.png',    // background of the "You stay in charge" section (spaces are fine)
}

export const MASCOT = {
  dog: '/images/mascot1.png',     // mas1
  cat: '/images/mascot2.png',     // mas2
  bunny: '/images/mascot3.png',   // mas3
  dragon: '/images/mascot4.png',  // mas4
  tester: '/images/mascot5.png',
}

// Head-only avatars (mas1..mas4): used in the agent feed, ticket list, empty states and the favicon
export const HEAD = {
  dragon: '/images/mas1.png',  // mas1 – startled "!!" dragon
  bunny: '/images/mas2.png',   // mas2
  cat: '/images/mas3.png',     // mas3
  dog: '/images/mas4.png',     // mas4 – sleeping dog with headphones
  shockcat: '/images/mas5.png',
  waiting: '/images/mas6.png',
}

// "How to use this website": step 1..4 = mas1..mas4
// "How to use this website": step 1..4 = mas1..mas4
export const STEP_IMG = [MASCOT.dog, MASCOT.cat, MASCOT.bunny, MASCOT.dragon,MASCOT.tester]   // full-body mascot images (unchanged)
export const STEP_MAS = ['/images/mas1.png', '/images/mas2.png', '/images/mas3.png', '/images/mas4.png','/images/mas5.png','/images/mas6.png']

// Ticket opened when a character on the board links to a ticket page (works with the sample data).
export const DEMO_TICKET_ID = 1
