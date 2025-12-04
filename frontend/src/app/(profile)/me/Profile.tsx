"use client";

import React, { JSX } from "react";

import {PersonalSection} from "@/app/(profile)/me/sections/PersonalSection";

export const Profile = (): JSX.Element => {
  console.log("[Profile Render] Proceeding to render profile content.");

  return (
    <>
      <PersonalSection />
      {/*<InvestmentsSection/>*/}
      {/*<TokensSection/>*/}
      {/*<GiftsSection/>*/}
    </>
  );
};
