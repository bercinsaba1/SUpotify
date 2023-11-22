import React from "react";
import UserPart from "./subcomponents/UserPart";
import Playlist from "./subcomponents/Playlist";
import FavoriteSongs90s from "./subcomponents/FavoriteSongs90s";
import FavoriteRecentSongs from "./subcomponents/FavoriteRecentSongs";
import MonthlyAverageRatingsChart from "./subcomponents/MonthlyAverageRatingsChart";
import SongsAddedByPerformerChart from "./subcomponents/SongsAddedByPerformerChart";

const ProfileMiddle = ({ lastPlaylists, userData, setCurrentPlace }) => {
  const handlePlaylistClick = (playlistName) => {
    setCurrentPlace("playlist");
    console.log(`Playlist clicked: ${playlistName}`);
    // Here you would handle the click event, such as navigating to the playlist page.
  };
  const handleButtonClick = () => {
    setCurrentPlace("submit-form");
    console.log("Button clicked");
  }
  const handleButtonClickE = () => {
    setCurrentPlace("submit-formE");
    console.log("Button clicked");
  }
  return (
    <>
      <div className="main-container">
        <div className="content-container">
          <UserPart userData={userData} />{" "}
          <button 
          onClick={handleButtonClick}
          className="add-song-btn">Add song to the database</button>
          <button 
          onClick={handleButtonClickE}
          className="add-song-btn">Delete song to the database</button>

          {/* UserPart bileşenini burada kullan */}
          <h2 className="last-played-title">Your Playlists </h2>
          
          <div className="lastPlaylists-container-forPP">
            {lastPlaylists.map((lastPlaylists, index) => (
              <Playlist
                key={index}
                name={lastPlaylists.name}
                thumbnail={lastPlaylists.thumbnail}
                onClick={() => handlePlaylistClick(lastPlaylists.name)}
              />
            ))}
          </div>
          <FavoriteSongs90s />
          <FavoriteRecentSongs />
          <MonthlyAverageRatingsChart />
          <SongsAddedByPerformerChart />
        </div>
      </div>
    </>
  );
};

export default ProfileMiddle;
