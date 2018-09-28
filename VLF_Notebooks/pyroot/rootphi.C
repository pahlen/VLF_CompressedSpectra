rootphi() {
  cout << "Ran rootphi.C" << endl;
}

float deltaPhi(float phi1, float phi2) {
  float PHI = phi1-phi2;
  if (PHI >= 3.14159265)
    PHI -= 2*3.14159265;
  else if (PHI < -3.14159265)
    PHI += 2*3.14159265;
 
    return PHI;
}

